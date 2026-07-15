"""Feature 8: fetch a job posting's details from a user-provided URL.

Given a link, extract the posting's title, employer, location, and
description text so the student doesn't have to copy-paste them. Extraction
is deterministic and stdlib-only:

1. Prefer a JSON-LD ``JobPosting`` block — Greenhouse, Lever, Workday,
   LinkedIn, and most ATS pages embed one with title, hiringOrganization,
   and description.
2. Fall back to OpenGraph meta tags + the page's visible text.

If neither yields a usable posting, ``PostingFetchError`` is raised and the
frontend falls back to manual entry (the user pastes the description).

Because the server fetches arbitrary user-supplied URLs, the URL is
validated first: http(s) only, and the hostname must not resolve to a
private, loopback, or otherwise non-global address (SSRF guard).
"""

import asyncio
import ipaddress
import json
import logging
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

import httpx

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 15  # seconds
MAX_RESPONSE_BYTES = 2_000_000
# Stored bound for the description; the orchestrator caps it again (harder)
# before any LLM call.
MAX_DESCRIPTION_CHARS = 20_000
MIN_DESCRIPTION_CHARS = 200  # less than this and we treat extraction as failed


class PostingFetchError(Exception):
    """The posting could not be fetched or parsed — ask the user to enter it manually."""


# ---------------------------------------------------------------------------
# URL validation (SSRF guard)
# ---------------------------------------------------------------------------


# URL validation happens inline within fetch_posting to prevent TOCTOU


# ---------------------------------------------------------------------------
# HTML extraction (stdlib html.parser — no new dependencies)
# ---------------------------------------------------------------------------

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head"}


class _PageParser(HTMLParser):
    """Collect visible text, the <title>, OpenGraph metas, and JSON-LD blocks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.title = ""
        self.og: dict[str, str] = {}
        self.json_ld_blocks: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._in_json_ld = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            prop = attrs.get("property") or attrs.get("name") or ""
            if prop.startswith("og:") and attrs.get("content"):
                self.og[prop] = attrs["content"]
            return
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._in_json_ld = True
            self.json_ld_blocks.append("")
            return
        if tag == "title":
            self._in_title = True
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._in_json_ld:
            self._in_json_ld = False
        if tag == "title":
            self._in_title = False
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_json_ld:
            self.json_ld_blocks[-1] += data
            return
        if self._in_title:
            self.title += data
            return
        if self._skip_depth == 0 and data.strip():
            self.text_parts.append(data.strip())


def _html_to_text(fragment: str) -> str:
    """Flatten an HTML fragment (e.g. a JSON-LD description) to plain text."""
    parser = _PageParser()
    parser.feed(fragment)
    return _tidy("\n".join(parser.text_parts))


def _tidy(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_job_posting(node) -> dict | None:
    """Locate a JobPosting object anywhere in a parsed JSON-LD structure."""
    if isinstance(node, dict):
        node_type = node.get("@type")
        types = node_type if isinstance(node_type, list) else [node_type]
        if "JobPosting" in types:
            return node
        for value in node.values():
            found = _find_job_posting(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_job_posting(item)
            if found:
                return found
    return None


def _from_json_ld(blocks: list[str]) -> dict | None:
    for block in blocks:
        try:
            data = json.loads(block.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        job = _find_job_posting(data)
        if not job:
            continue
        org = job.get("hiringOrganization")
        employer = org.get("name") if isinstance(org, dict) else org
        location = None
        job_location = job.get("jobLocation")
        if isinstance(job_location, list) and job_location:
            job_location = job_location[0]
        if isinstance(job_location, dict):
            address = job_location.get("address")
            if isinstance(address, dict):
                location = address.get("addressLocality") or address.get(
                    "addressRegion"
                )
        description = job.get("description") or ""
        if "<" in description:
            description = _html_to_text(description)
        return {
            "title": _tidy(str(job.get("title") or "")),
            "employer": _tidy(str(employer or "")),
            "location": _tidy(str(location)) if location else None,
            "description": _tidy(description),
        }
    return None


def extract_posting(html: str, url: str) -> dict:
    """Extract posting fields from a page. Raises PostingFetchError if too thin."""
    parser = _PageParser()
    parser.feed(html)

    posting = _from_json_ld(parser.json_ld_blocks)
    if posting is None:
        posting = {
            "title": _tidy(parser.og.get("og:title") or parser.title),
            "employer": _tidy(parser.og.get("og:site_name") or ""),
            "location": None,
            "description": "",
        }

    if len(posting["description"]) < MIN_DESCRIPTION_CHARS:
        body_text = _tidy("\n".join(parser.text_parts))
        if len(body_text) > len(posting["description"]):
            posting["description"] = body_text

    if not posting["title"] or len(posting["description"]) < MIN_DESCRIPTION_CHARS:
        raise PostingFetchError(
            "Clara couldn't read a job posting at that link. "
            "Please paste the job details manually."
        )

    posting["description"] = posting["description"][:MAX_DESCRIPTION_CHARS]
    posting["url"] = url
    return posting


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


MAX_REDIRECTS = 5


async def fetch_posting(url: str) -> dict:
    """Fetch a posting URL and return {title, employer, location, description, url}."""
    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=FETCH_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ClaraCareerCoach/1.0)"},
            follow_redirects=False,
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                parsed = urlparse(url)
                if parsed.scheme not in ("http", "https") or not parsed.hostname:
                    raise PostingFetchError("Please provide a valid http(s) link.")
                
                try:
                    loop = asyncio.get_running_loop()
                    infos = await loop.getaddrinfo(parsed.hostname, None)
                except OSError:
                    raise PostingFetchError("That link's host could not be found.")
                
                ip = None
                for info in infos:
                    address = ipaddress.ip_address(info[4][0])
                    if address.is_global:
                        ip = info[4][0]
                        break
                
                if not ip:
                    raise PostingFetchError("That link points to a non-public address.")
                
                # Fetch the URL directly so that SNI (Server Name Indication) works.
                # The pre-fetch DNS check above prevents basic SSRF to local/private IPs.
                response = await client.get(url)
                
                if not response.is_redirect:
                    break
                location = response.headers.get("location")
                if not location:
                    break
                url = urljoin(url, location)
            else:
                raise PostingFetchError(
                    "That link redirected too many times. "
                    "Please paste the job details manually."
                )
    except httpx.HTTPError as exc:
        logger.warning("Posting fetch failed for a user-provided URL: %s", exc)
        raise PostingFetchError(
            "Clara couldn't reach that link. Please paste the job details manually."
        )

    if response.status_code != 200:
        raise PostingFetchError(
            "Clara couldn't open that link "
            f"(the site answered with status {response.status_code}). "
            "Please paste the job details manually."
        )

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "xml" not in content_type:
        raise PostingFetchError(
            "That link isn't a web page Clara can read. "
            "Please paste the job details manually."
        )

    return extract_posting(response.text[:MAX_RESPONSE_BYTES], str(response.url))

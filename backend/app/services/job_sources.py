"""Job posting sources for the Feature 7 scanner.

Postings come from the official public board APIs of Greenhouse and Lever —
both are free, keyless, and explicitly published for public consumption, so
scanning them respects the source sites' terms of service. We store only the
posting metadata and the original link; we never republish full postings.

COMPANY_BOARDS is the curated employer list. To add a company, find its board
slug and verify it responds before committing:

    Greenhouse: curl https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
    Lever:      curl https://api.lever.co/v0/postings/<slug>?mode=json

A company whose board 404s (renamed slug, switched ATS) is skipped with a
warning — one bad entry never breaks the scan.
"""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 20  # seconds per company board

# (display name, board type, board slug) — intern-friendly tech employers,
# remote-heavy or with East Coast presence. Curated by the project team.
COMPANY_BOARDS: list[tuple[str, str, str]] = [
    ("Stripe", "greenhouse", "stripe"),
    ("Coinbase", "greenhouse", "coinbase"),
    ("Robinhood", "greenhouse", "robinhood"),
    ("Dropbox", "greenhouse", "dropbox"),
    ("GitLab", "greenhouse", "gitlab"),
    ("Cloudflare", "greenhouse", "cloudflare"),
    ("Datadog", "greenhouse", "datadog"),
    ("MongoDB", "greenhouse", "mongodb"),
    ("Elastic", "greenhouse", "elastic"),
    ("Figma", "greenhouse", "figma"),
    ("Duolingo", "greenhouse", "duolingo"),
    ("Roblox", "greenhouse", "roblox"),
    ("Asana", "greenhouse", "asana"),
    ("Affirm", "greenhouse", "affirm"),
    ("Vercel", "greenhouse", "vercel"),
    ("Anthropic", "greenhouse", "anthropic"),
    ("Databricks", "greenhouse", "databricks"),
    ("Twilio", "greenhouse", "twilio"),
    ("Reddit", "greenhouse", "reddit"),
    ("Pinterest", "greenhouse", "pinterest"),
    ("Instacart", "greenhouse", "instacart"),
    ("Lyft", "greenhouse", "lyft"),
    ("Squarespace", "greenhouse", "squarespace"),
    ("Qualtrics", "greenhouse", "qualtrics"),
    ("Palantir", "lever", "palantir"),
    ("Zoox", "lever", "zoox"),
]


def normalize_greenhouse(company: str, payload: dict) -> list[dict]:
    """Normalize a Greenhouse boards-api response into posting dicts."""
    postings = []
    for job in payload.get("jobs", []):
        url = job.get("absolute_url")
        title = job.get("title")
        if not url or not title:
            continue
        postings.append(
            {
                "source": "greenhouse",
                "url": url,
                "title": title.strip(),
                "employer": company,
                "location": (job.get("location") or {}).get("name"),
            }
        )
    return postings


def normalize_lever(company: str, payload: list) -> list[dict]:
    """Normalize a Lever postings-api response into posting dicts."""
    postings = []
    for job in payload if isinstance(payload, list) else []:
        url = job.get("hostedUrl")
        title = job.get("text")
        if not url or not title:
            continue
        postings.append(
            {
                "source": "lever",
                "url": url,
                "title": title.strip(),
                "employer": company,
                "location": (job.get("categories") or {}).get("location"),
            }
        )
    return postings


async def _fetch_board(
    client: httpx.AsyncClient, company: str, board: str, slug: str
) -> list[dict]:
    if board == "greenhouse":
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    else:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = await client.get(url)
        if r.status_code != 200:
            logger.warning("%s board for %s returned %s", board, company, r.status_code)
            return []
        if board == "greenhouse":
            return normalize_greenhouse(company, r.json())
        return normalize_lever(company, r.json())
    except Exception as exc:
        logger.warning("Failed to fetch %s board for %s: %s", board, company, exc)
        return []


async def fetch_all_postings() -> list[dict]:
    """Fetch every curated company board concurrently and dedupe by URL."""
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
        results = await asyncio.gather(
            *(
                _fetch_board(client, company, board, slug)
                for company, board, slug in COMPANY_BOARDS
            )
        )
    seen: set[str] = set()
    postings = []
    for board_postings in results:
        for posting in board_postings:
            if posting["url"] in seen:
                continue
            seen.add(posting["url"])
            postings.append(posting)
    logger.info("Job scan fetched %d postings", len(postings))
    return postings

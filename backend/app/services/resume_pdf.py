"""Typst-rendered resume PDFs.

Renders a generated resume document (title + sections, or the student's
edited text) to a clean one-page PDF via Typst. Layout is adapted from the
career-ops CV template: New Computer Modern 11pt on US letter, tight
margins, bold ruled section headings, hanging bullet indents.

One-page guarantee: compile at 11pt and, if the result overflows a page,
recompile at progressively smaller font sizes / tighter leading until it
fits (floor 9pt). If it still overflows at the floor, the multi-page PDF is
returned rather than clipping content — the UI's copy-text fallback always
remains available.

Typst bundles New Computer Modern, so no font files are needed at runtime.
"""

import io
import os
import tempfile

import typst
from pypdf import PdfReader

# (font size pt, leading em) — tried in order until the resume fits one page.
_FIT_STEPS = [(11.0, 0.65), (10.5, 0.60), (10.0, 0.55), (9.5, 0.50), (9.0, 0.45)]

_BULLET_PREFIXES = ("- ", "* ", "• ", "– ", "— ")

# Characters with markup meaning in Typst text mode.
_TYPST_SPECIAL = set("\\#$[]{}*_`<>@~/")


def _escape(text: str) -> str:
    return "".join(f"\\{ch}" if ch in _TYPST_SPECIAL else ch for ch in text)


def _render_lines(text: str) -> str:
    """Render plain text as Typst markup: bullet lines get hanging indents,
    other lines become paragraphs."""
    parts = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        bullet = None
        for prefix in _BULLET_PREFIXES:
            if line.startswith(prefix):
                bullet = line[len(prefix) :].strip()
                break
        if bullet is not None:
            parts.append(
                "#grid(columns: (0.25in, 1fr), align: (right + top, left + top), "
                f"[•], [{_escape(bullet)}])"
            )
        else:
            parts.append(_escape(line) + " \\")
    return "\n".join(parts)


def build_resume_typ(
    student_name: str,
    sections: list[dict],
    edited_text: str | None,
    font_size: float,
    leading: float,
) -> str:
    """Build the full Typst source for one resume."""
    body_parts = []
    if edited_text:
        body_parts.append(_render_lines(edited_text))
    else:
        for section in sections:
            heading = (section.get("heading") or "").strip()
            content = section.get("content") or ""
            if heading:
                body_parts.append(f"#cv-section[{_escape(heading)}]")
            if content:
                body_parts.append(_render_lines(content))
    body = "\n\n".join(body_parts)

    # Header is the student's name only — never the target job title, so the
    # document reads as their resume rather than one labeled for a posting.
    header = f'#text(size: 17pt, weight: "bold")[{_escape(student_name)}] \\'

    return f"""#set page(
  paper: "us-letter",
  margin: (top: 0.4in, bottom: 0.35in, left: 0.45in, right: 0.45in),
)
#set text(font: "New Computer Modern", size: {font_size}pt)
#set par(leading: {leading}em, spacing: 0.45em)

#let cv-section(title) = {{
  v(6pt)
  text(size: {font_size * 1.2}pt, weight: "bold")[#title]
  v(-1pt)
  line(length: 100%, stroke: 0.5pt + black)
  v(4pt)
}}

#align(center)[
{header}
]
#v(2pt)

{body}
"""


def _compile(typ_source: str, format: str = "pdf", ppi: float | None = None) -> bytes:
    """Compile Typst source via a temp file. Returns bytes for one page;
    multi-page PNG output comes back as a list, in which case the first
    page is returned."""
    fd, path = tempfile.mkstemp(suffix=".typ")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(typ_source)
        kwargs = {"format": format}
        if ppi is not None:
            kwargs["ppi"] = ppi
        result = typst.compile(path, **kwargs)
        return result[0] if isinstance(result, list) else result
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _page_count(pdf_bytes: bytes) -> int:
    return len(PdfReader(io.BytesIO(pdf_bytes)).pages)


def _fit_to_one_page(
    student_name: str,
    sections: list[dict],
    edited_text: str | None,
) -> tuple[str, bytes]:
    """Find the largest type size that fits one page. Returns the fitted
    Typst source and its compiled PDF."""
    source, pdf = "", b""
    for font_size, leading in _FIT_STEPS:
        source = build_resume_typ(
            student_name, sections, edited_text, font_size, leading
        )
        pdf = _compile(source)
        if _page_count(pdf) <= 1:
            break
    return source, pdf


def render_resume_pdf(
    student_name: str,
    sections: list[dict],
    edited_text: str | None = None,
) -> bytes:
    """Render a resume to a PDF, shrinking type until it fits one page.

    Raises typst-level exceptions on compile failure — callers surface a
    friendly error and the UI falls back to copy-text.
    """
    _, pdf = _fit_to_one_page(student_name, sections, edited_text)
    return pdf


def render_resume_png(
    student_name: str,
    sections: list[dict],
    edited_text: str | None = None,
    ppi: float = 144.0,
) -> bytes:
    """Render the same fitted resume as a PNG image — used by the frontend
    to show a clean preview without the browser's PDF viewer chrome."""
    source, _ = _fit_to_one_page(student_name, sections, edited_text)
    return _compile(source, format="png", ppi=ppi)

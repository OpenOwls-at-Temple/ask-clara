"""Text extraction from uploaded PDF / DOCX files.

Parsing is CPU-bound; callers on the async path should run
`parse_document` in a threadpool.
"""

import io


class UnsupportedFileTypeError(ValueError):
    """Raised when an uploaded file is neither a PDF nor a DOCX."""


def parse_document(content: bytes, content_type: str, filename: str) -> str:
    """Extract plain text from a PDF or DOCX file."""
    ext = (filename or "").rsplit(".", 1)[-1].lower()
    if content_type == "application/pdf" or ext == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx" or "wordprocessingml" in content_type:
        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    raise UnsupportedFileTypeError("Unsupported file type. Upload a PDF or DOCX.")

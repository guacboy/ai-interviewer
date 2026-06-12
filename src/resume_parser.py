"""Resume text extraction from PDF files or plain text."""

from pathlib import Path

import pdfplumber


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract all text content from a PDF resume."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                
    return "\n".join(text_parts)


def load_resume(source: str | Path) -> str:
    """Load resume text from a PDF path, a text file path, or raw pasted text.

    If `source` points to an existing PDF file, its text is extracted.
    If `source` points to an existing text file, it is read directly.
    Otherwise, `source` is treated as raw resume text and returned as-is.
    """
    path = Path(source)
    if path.suffix.lower() == ".pdf" and path.is_file():
        return extract_text_from_pdf(path)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    
    return str(source)

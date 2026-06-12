"""Tests for resume_parser."""

from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from resume_parser import extract_text_from_pdf, load_resume


def _write_pdf(path: Path, pages: list[list[str]]) -> None:
    c = canvas.Canvas(str(path))
    for lines in pages:
        y = 750
        for line in lines:
            c.drawString(72, y, line)
            y -= 20
        c.showPage()
    c.save()


@pytest.fixture
def single_page_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "resume.pdf"
    _write_pdf(pdf_path, [["John Doe", "Software Engineer"]])
    return pdf_path


@pytest.fixture
def multipage_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "resume.pdf"
    _write_pdf(pdf_path, [["Page one text"], ["Page two text"]])
    return pdf_path


@pytest.fixture
def blank_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "blank.pdf"
    _write_pdf(pdf_path, [[]])
    return pdf_path


class TestExtractTextFromPdf:
    def test_single_page(self, single_page_pdf: Path):
        text = extract_text_from_pdf(single_page_pdf)
        assert "John Doe" in text
        assert "Software Engineer" in text

    def test_multipage_joins_all_pages(self, multipage_pdf: Path):
        text = extract_text_from_pdf(multipage_pdf)
        assert "Page one text" in text
        assert "Page two text" in text

    def test_blank_pdf_returns_empty_string(self, blank_pdf: Path):
        assert extract_text_from_pdf(blank_pdf) == ""

    def test_accepts_string_path(self, single_page_pdf: Path):
        text = extract_text_from_pdf(str(single_page_pdf))
        assert "John Doe" in text


class TestLoadResume:
    def test_pdf_path(self, single_page_pdf: Path):
        text = load_resume(single_page_pdf)
        assert "John Doe" in text

    def test_pdf_path_uppercase_extension(self, tmp_path: Path, single_page_pdf: Path):
        upper_path = tmp_path / "resume.PDF"
        upper_path.write_bytes(single_page_pdf.read_bytes())
        text = load_resume(upper_path)
        assert "John Doe" in text

    def test_text_file_path(self, tmp_path: Path):
        text_path = tmp_path / "resume.txt"
        text_path.write_text("Jane Doe - Data Scientist", encoding="utf-8")
        assert load_resume(text_path) == "Jane Doe - Data Scientist"

    def test_raw_pasted_text(self):
        raw = "Jane Doe\nData Scientist with 5 years of experience"
        assert load_resume(raw) == raw

    def test_empty_string(self):
        assert load_resume("") == ""

    def test_nonexistent_pdf_path_treated_as_raw_text(self):
        source = "nonexistent_resume.pdf"
        assert load_resume(source) == source

    def test_nonexistent_path_object_treated_as_raw_text(self):
        fake = Path("not_a_real_file.txt")
        assert load_resume(fake) == str(fake)

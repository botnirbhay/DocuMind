from app.services.ingestion import extract_docx_sections, extract_pdf_sections, extract_txt_sections
from tests.helpers import build_docx_bytes, build_pdf_bytes


def test_pdf_text_extraction_returns_page_metadata() -> None:
    content = build_pdf_bytes(["Hello PDF World", "Second line"])

    sections = extract_pdf_sections(content)

    assert len(sections) == 1
    assert sections[0].page_number == 1
    assert "Hello PDF World" in sections[0].text
    assert "Second line" in sections[0].text


def test_docx_text_extraction_preserves_paragraphs() -> None:
    content = build_docx_bytes(["First paragraph", "Second paragraph"])

    sections = extract_docx_sections(content)

    assert len(sections) == 1
    assert sections[0].page_number is None
    assert sections[0].text == "First paragraph\n\nSecond paragraph"


def test_txt_text_extraction_normalizes_whitespace() -> None:
    content = b"Line one   with extra spaces\r\n\r\nLine two"

    sections = extract_txt_sections(content)

    assert len(sections) == 1
    assert sections[0].text == "Line one with extra spaces\n\nLine two"

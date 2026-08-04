from pathlib import Path

import pytest

from app.services.parsers import ResumeParseError, extract_text


def test_resume_parser_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("candidate")

    with pytest.raises(ResumeParseError, match="Unsupported"):
        extract_text(path)


def test_resume_parser_rejects_empty_pdf(tmp_path):
    path = tmp_path / "empty.pdf"
    path.write_bytes(b"%PDF-1.4")

    with pytest.raises(ResumeParseError):
        extract_text(path)


def test_resume_parser_extracts_docx_text(tmp_path):
    from docx import Document

    path = tmp_path / "resume.docx"
    document = Document()
    document.add_paragraph("Python backend engineer")
    document.save(path)

    assert "Python backend engineer" in extract_text(path)

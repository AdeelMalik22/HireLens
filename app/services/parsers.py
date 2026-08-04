from pathlib import Path

import fitz
from docx import Document

from app.services.exceptions import ServiceError


class ResumeParseError(ServiceError):
    pass


def extract_text(path: Path) -> str:
    try:
        if path.suffix.lower() == ".pdf":
            with fitz.open(path) as document:
                text = "\n".join(page.get_text() for page in document)
        elif path.suffix.lower() == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
        else:
            raise ResumeParseError("Unsupported resume format")
        text = text.strip()
        if not text:
            raise ResumeParseError("Resume contains no readable text")
        return text
    except ResumeParseError:
        raise
    except Exception as error:
        raise ResumeParseError("Unable to extract resume text") from error

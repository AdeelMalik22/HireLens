from pathlib import Path

import pytest

from app.services.parsers import ResumeParseError, extract_text


def test_resume_parser_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("candidate")

    with pytest.raises(ResumeParseError, match="Unsupported"):
        extract_text(path)

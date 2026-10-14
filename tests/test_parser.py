"""
Unit Tests for RequirementParser and TestCaseLoader Service.
"""

import json
import pytest
from pathlib import Path
from services.parser import RequirementParser, TestCaseLoader
from models.requirement import Requirement
from models.testcase import TestCase
from utils.exceptions import RequirementParseError, TestCaseLoadError


def test_parse_json_requirements(tmp_path: Path):
    """Tests parsing valid structured requirements from JSON file."""
    req_file = tmp_path / "requirements.json"
    data = [
        {"id": "REQ-101", "requirement": "Customer can login with valid email."},
        {"id": "REQ-102", "requirement": "Customer can reset password via email link."},
    ]
    req_file.write_text(json.dumps(data), encoding="utf-8")

    parser = RequirementParser()
    requirements = parser.parse_file(req_file)

    assert len(requirements) == 2
    assert requirements[0].id == "REQ-101"
    assert "login" in requirements[0].requirement.lower()
    assert requirements[1].id == "REQ-102"


def test_parse_txt_requirements(tmp_path: Path):
    """Tests parsing functional requirements from plain TXT file."""
    req_file = tmp_path / "requirements.txt"
    text_content = (
        "Customer can login.\n"
        "Customer can reset password.\n"
        "Customer can logout."
    )
    req_file.write_text(text_content, encoding="utf-8")

    parser = RequirementParser()
    requirements = parser.parse_file(req_file)

    assert len(requirements) == 3
    assert requirements[0].id == "REQ-001"
    assert requirements[0].requirement == "Customer can login."
    assert requirements[1].id == "REQ-002"
    assert requirements[1].requirement == "Customer can reset password."
    assert requirements[2].id == "REQ-003"
    assert requirements[2].requirement == "Customer can logout."


def test_parse_docx_requirements(tmp_path: Path):
    """Tests parsing requirements from Microsoft Word (.docx) document."""
    try:
        import docx
    except ImportError:
        pytest.skip("python-docx library not installed")

    docx_path = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_paragraph("Customer can login to dashboard.")
    doc.add_paragraph("System locks account after 5 failed attempts.")
    doc.save(docx_path)

    parser = RequirementParser()
    requirements = parser.parse_file(docx_path)

    assert len(requirements) == 2
    assert requirements[0].id == "REQ-001"
    assert "login" in requirements[0].requirement.lower()


def test_parse_pdf_requirements(tmp_path: Path):
    """Tests parsing requirements from PDF (.pdf) document using PyMuPDF."""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            pytest.skip("PyMuPDF (pymupdf) library not installed")

    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "REQ-001: Customer can login.\nREQ-002: Customer can reset password.")
    doc.save(pdf_path)
    doc.close()

    parser = RequirementParser()
    requirements = parser.parse_file(pdf_path)

    assert len(requirements) >= 2
    assert any("login" in r.requirement.lower() for r in requirements)


def test_parse_empty_file(tmp_path: Path):
    """Tests that empty file raises RequirementParseError."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    parser = RequirementParser()
    with pytest.raises(RequirementParseError) as exc_info:
        parser.parse_file(empty_file)

    assert "Empty document" in str(exc_info.value)


def test_parse_missing_file():
    """Tests that missing file path raises RequirementParseError."""
    parser = RequirementParser()
    with pytest.raises(RequirementParseError) as exc_info:
        parser.parse_file("non_existent_requirements_file_12345.txt")

    assert "Missing file" in str(exc_info.value)


def test_parse_unsupported_extension(tmp_path: Path):
    """Tests that unsupported file format raises RequirementParseError."""
    unsupported_file = tmp_path / "data.csv"
    unsupported_file.write_text("col1,col2\nval1,val2", encoding="utf-8")

    parser = RequirementParser()
    with pytest.raises(RequirementParseError) as exc_info:
        parser.parse_file(unsupported_file)

    assert "Unsupported file type" in str(exc_info.value)


def test_parse_invalid_json(tmp_path: Path):
    """Tests that corrupted/malformed JSON raises RequirementParseError."""
    invalid_json = tmp_path / "bad.json"
    invalid_json.write_text("{bad_json_content...", encoding="utf-8")

    parser = RequirementParser()
    with pytest.raises(RequirementParseError) as exc_info:
        parser.parse_file(invalid_json)

    assert "JSON parsing failure" in str(exc_info.value)


def test_parse_deduplication_and_sequence_ids(tmp_path: Path):
    """Tests deduplication of identical requirements and sequential REQ ID generation."""
    req_file = tmp_path / "dups.txt"
    text_content = (
        "Customer can login.\n"
        "Customer can login.\n"  # Duplicate
        "  \n"  # Empty whitespace line
        "Customer can logout."
    )
    req_file.write_text(text_content, encoding="utf-8")

    parser = RequirementParser(req_id_prefix="REQ")
    requirements = parser.parse_file(req_file)

    assert len(requirements) == 2
    assert requirements[0].id == "REQ-001"
    assert requirements[0].requirement == "Customer can login."
    assert requirements[1].id == "REQ-002"
    assert requirements[1].requirement == "Customer can logout."


def test_nlp_preprocessing_options(tmp_path: Path):
    """Tests NLP preprocessing options (lowercase, stopword removal)."""
    req_file = tmp_path / "nlp.txt"
    req_file.write_text("Customer Can Reset Password via Email Link.", encoding="utf-8")

    parser = RequirementParser()
    requirements = parser.parse_file(req_file, lowercase=True)

    assert len(requirements) == 1
    assert requirements[0].requirement == "customer can reset password via email link."


def test_load_testcases_json(tmp_path: Path):
    """Tests TestCaseLoader functionality."""
    tc_file = tmp_path / "testcases.json"
    tc_data = [
        {
            "id": "TC101",
            "title": "Login Test",
            "description": "Verify login functionality",
            "steps": ["Step 1", "Step 2"],
            "expected_result": "Logged in",
            "priority": "High",
            "requirement_id": "REQ-101",
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    testcases = TestCaseLoader.load_from_json(tc_file)

    assert len(testcases) == 1
    tc = testcases[0]
    assert tc.id == "TC101"
    assert tc.title == "Login Test"
    assert len(tc.steps) == 2
    assert tc.priority == "High"

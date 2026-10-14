"""
Unit Tests for Manual Test Case Loader Service (Module 2).
"""

import json
import pytest
from pathlib import Path

from services.testcase_loader import TestCaseLoader
from models.testcase import TestCase, PriorityLevel
from utils.exceptions import TestCaseLoadError


def test_valid_testcase_loading(tmp_path: Path):
    """Tests loading valid test case entries from JSON."""
    tc_file = tmp_path / "testcases.json"
    tc_data = [
        {
            "id": "TC001",
            "title": "Verify valid login",
            "description": "Verify user can login with valid credentials",
            "steps": [
                "Open login page",
                "Enter email",
                "Enter password",
                "Click login"
            ],
            "expected_result": "Dashboard should appear",
            "priority": "High",
            "requirement_ids": ["REQ-001"]
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader()
    testcases = loader.load_json(tc_file)

    assert len(testcases) == 1
    tc = testcases[0]
    assert tc.id == "TC001"
    assert tc.title == "Verify valid login"
    assert len(tc.steps) == 4
    assert tc.priority == "High"
    assert tc.requirement_ids == ["REQ-001"]
    assert tc.requirement_id == "REQ-001"


def test_multiple_testcases_loading(tmp_path: Path):
    """Tests loading multiple valid test cases from JSON list."""
    tc_file = tmp_path / "multiple_tcs.json"
    tc_data = [
        {
            "id": "TC001",
            "title": "Valid Login",
            "description": "User login test",
            "steps": ["Step 1"],
            "expected_result": "Dashboard displayed",
            "priority": "Critical",
            "requirement_ids": ["REQ-001"]
        },
        {
            "id": "TC002",
            "title": "Account Lockout",
            "description": "Verify lockout",
            "steps": ["Step 1", "Step 2"],
            "expected_result": "Locked error prompt",
            "priority": "Medium",
            "requirement_ids": ["REQ-002"]
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader()
    testcases = loader.load_json(tc_file)

    assert len(testcases) == 2
    assert testcases[0].id == "TC001"
    assert testcases[1].id == "TC002"
    assert testcases[0].priority == "Critical"
    assert testcases[1].priority == "Medium"


def test_invalid_json_format(tmp_path: Path):
    """Tests that malformed JSON raises TestCaseLoadError."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{invalid_json_structure...", encoding="utf-8")

    loader = TestCaseLoader()
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json(bad_json)

    assert "Invalid JSON format" in str(exc_info.value)


def test_missing_mandatory_field(tmp_path: Path):
    """Tests that missing mandatory fields (id, title, description, expected_result) raise TestCaseLoadError in strict mode."""
    tc_file = tmp_path / "missing_title.json"
    tc_data = [
        {
            "id": "TC001",
            # "title" missing
            "description": "Description without title",
            "steps": ["Step 1"],
            "expected_result": "Result",
            "priority": "High"
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader(strict=True)
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json(tc_file)

    assert "Missing field 'title'" in str(exc_info.value)


def test_duplicate_ids(tmp_path: Path):
    """Tests that duplicate testcase IDs raise TestCaseLoadError."""
    tc_file = tmp_path / "dups.json"
    tc_data = [
        {
            "id": "TC001",
            "title": "First Test",
            "description": "Desc 1",
            "steps": ["Step 1"],
            "expected_result": "Res 1",
            "priority": "High"
        },
        {
            "id": "TC001",  # Duplicate ID
            "title": "Second Test",
            "description": "Desc 2",
            "steps": ["Step 1"],
            "expected_result": "Res 2",
            "priority": "Low"
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader(strict=True)
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json(tc_file)

    assert "Duplicate testcase IDs not allowed" in str(exc_info.value)


def test_invalid_priority(tmp_path: Path):
    """Tests that invalid priority level raises TestCaseLoadError in strict mode."""
    tc_file = tmp_path / "bad_priority.json"
    tc_data = [
        {
            "id": "TC001",
            "title": "Title",
            "description": "Desc",
            "steps": ["Step 1"],
            "expected_result": "Result",
            "priority": "SuperUltraHigh"  # Invalid priority
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader(strict=True)
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json(tc_file)

    assert "Invalid priority" in str(exc_info.value)


def test_empty_steps(tmp_path: Path):
    """Tests that empty steps list raises TestCaseLoadError in strict mode."""
    tc_file = tmp_path / "empty_steps.json"
    tc_data = [
        {
            "id": "TC001",
            "title": "Title",
            "description": "Desc",
            "steps": [],  # Empty steps list
            "expected_result": "Result",
            "priority": "High"
        }
    ]
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    loader = TestCaseLoader(strict=True)
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json(tc_file)

    assert "Empty steps" in str(exc_info.value)


def test_missing_file_handling():
    """Tests that non-existent file path raises TestCaseLoadError."""
    loader = TestCaseLoader()
    with pytest.raises(TestCaseLoadError) as exc_info:
        loader.load_json("non_existent_testcase_file.json")

    assert "File not found" in str(exc_info.value)

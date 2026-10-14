"""
Unit Tests for AI Validation Engine Service (Module 5).
"""

import pytest
from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import ValidationStatus, DuplicateMatch, CoverageResult
from services.validator import ValidationEngine


def test_valid_testcase():
    """Tests a fully valid testcase meeting all compliance rules."""
    tc = TestCase(
        id="TC001",
        title="Verify User Login Functionality",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=["Open login page", "Enter valid credentials", "Click Login button"],
        expected_result="User dashboard is displayed successfully.",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    req = Requirement(id="REQ-001", requirement="Customer can login into the application.")
    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc], requirements=[req])

    assert len(results) == 1
    res = results[0]
    assert res.status == ValidationStatus.PASS
    assert res.score == 100
    assert len(res.errors) == 0
    assert len(res.warnings) == 0


def test_missing_title():
    """Tests Rule 1 failure when title is missing."""
    tc = TestCase(
        id="TC001",
        title="",  # Missing title
        description="Verify user can login with valid credentials.",
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("Title is missing" in err for err in res.errors)
    assert res.score < 100


def test_missing_description():
    """Tests Rule 2 failure when description is missing."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="",  # Missing description
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("Description is missing" in err for err in res.errors)


def test_missing_steps():
    """Tests Rule 3 failure when steps list is empty."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=[],  # Empty steps
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("at least one step" in err for err in res.errors)


def test_missing_expected_result():
    """Tests Rule 4 failure when expected result is missing."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=["Step 1"],
        expected_result="",  # Missing expected result
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("Expected result is missing" in err for err in res.errors)


def test_invalid_priority():
    """Tests Rule 5 failure when priority level is invalid."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="SuperHighPriority",  # Invalid
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("Priority" in err for err in res.errors)


def test_requirement_not_mapped():
    """Tests Rule 6 failure when testcase is unmapped to any requirement."""
    tc = TestCase(
        id="TC001",
        title="Unmapped Test",
        description="Verify user can update profile details cleanly.",
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=[],  # Unmapped
    )

    engine = ValidationEngine()
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.FAIL
    assert any("Requirement mapping missing" in err for err in res.errors)


def test_duplicate_testcase():
    """Tests Rule 7 warning when testcase is detected as a duplicate."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    dup_match = DuplicateMatch(
        tc1_id="TC001",
        tc2_id="TC004",
        similarity_score=0.91,
        similarity_percentage=91.0,
        is_duplicate=True,
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc], duplicate_results=[dup_match])

    res = results[0]
    assert res.status == ValidationStatus.WARNING
    assert res.is_duplicate is True
    assert "TC004" in res.duplicate_with
    assert any("Possible duplicate of TC004" in warn for warn in res.warnings)


def test_short_description():
    """Tests Rule 8 warning when description is too short."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Short desc",  # < 15 chars
        steps=["Step 1"],
        expected_result="Valid expected result",
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"], min_description_length=15)
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.WARNING
    assert any("Description is too short" in warn for warn in res.warnings)


def test_poor_expected_result():
    """Tests Rule 9 warning when expected result is vague ("Success", "OK")."""
    tc = TestCase(
        id="TC001",
        title="Login Test",
        description="Verify registered user can log into dashboard with valid credentials.",
        steps=["Step 1"],
        expected_result="Success",  # Vague expected result
        priority="High",
        requirement_ids=["REQ-001"],
    )

    engine = ValidationEngine(valid_req_ids=["REQ-001"])
    results = engine.validate_testcases([tc])

    res = results[0]
    assert res.status == ValidationStatus.WARNING
    assert any("Expected result is too vague" in warn for warn in res.warnings)

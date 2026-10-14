"""
Unit Tests for AI Requirement Coverage Checker Service (Module 4).
"""

import pytest
from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import CoverageResult
from services.coverage_checker import CoverageChecker
from utils.exceptions import CoverageCheckError


def test_100_percent_coverage():
    """Tests 100% requirement coverage calculation."""
    reqs = [
        Requirement(id="REQ-001", requirement="Customer can login into the application."),
        Requirement(id="REQ-002", requirement="System locks user account after 5 failed attempts."),
    ]

    tcs = [
        TestCase(
            id="TC001",
            title="User Login Test",
            description="Verify login functionality",
            steps=["Open page", "Enter credentials", "Click login"],
            expected_result="User dashboard displayed",
            priority="High",
            requirement_ids=["REQ-001"],
        ),
        TestCase(
            id="TC002",
            title="Account Lockout Test",
            description="Verify lockout functionality after failed attempts",
            steps=["Enter wrong password 5 times"],
            expected_result="Account locked message shown",
            priority="High",
            requirement_ids=["REQ-002"],
        ),
    ]

    checker = CoverageChecker()
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 100.0
    assert res.covered_requirements_count == 2
    assert len(res.missing_requirements) == 0
    assert "REQ-001" in res.covered_requirements
    assert "REQ-002" in res.covered_requirements
    assert res.mapping["REQ-001"] == ["TC001"]
    assert res.mapping["REQ-002"] == ["TC002"]


def test_partial_coverage():
    """Tests partial requirement coverage calculation."""
    reqs = [
        Requirement(id="REQ-001", requirement="Customer can login into the application."),
        Requirement(id="REQ-002", requirement="System locks user account after 5 failed attempts."),
        Requirement(id="REQ-003", requirement="Customer can reset password via email verification link."),
    ]

    tcs = [
        TestCase(
            id="TC001",
            title="User Login Test",
            description="Verify login functionality",
            steps=["Step 1"],
            expected_result="Result",
            priority="High",
            requirement_ids=["REQ-001"],
        )
    ]

    checker = CoverageChecker()
    res = checker.check_coverage(reqs, tcs)

    assert res.covered_requirements_count == 1
    assert res.coverage_percentage == 33.33
    assert "REQ-001" in res.covered_requirements
    assert "REQ-002" in res.missing_requirements
    assert "REQ-003" in res.missing_requirements


def test_no_coverage():
    """Tests 0% coverage when no test cases map to requirements."""
    reqs = [
        Requirement(id="REQ-001", requirement="Customer can update user profile details."),
        Requirement(id="REQ-002", requirement="System sends email notification on profile change."),
    ]

    tcs = []  # No test cases

    checker = CoverageChecker()
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 0.0
    assert res.covered_requirements_count == 0
    assert len(res.missing_requirements) == 2


def test_explicit_mapping():
    """Tests coverage determined via Phase 1 explicit requirement_ids."""
    reqs = [Requirement(id="REQ-101", requirement="System shall support user logout.")]
    tcs = [
        TestCase(
            id="TC101",
            title="Logout Test",
            description="Verify logout",
            steps=["Click logout"],
            expected_result="Logged out",
            priority="Low",
            requirement_ids=["REQ-101"],
        )
    ]

    checker = CoverageChecker()
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 100.0
    assert res.mapping["REQ-101"] == ["TC101"]


def test_semantic_matching():
    """Tests coverage determined via Phase 2 semantic AI matching when explicit mapping is missing."""
    reqs = [
        Requirement(
            id="REQ-201",
            requirement="System shall allow users to search products by title, category, and price range.",
        )
    ]

    # Testcase has NO explicit requirement_ids mapping
    tcs = [
        TestCase(
            id="TC201",
            title="Product Search Functionality Test",
            description="Verify user can search products by title, category filter, and price range.",
            steps=["Open search bar", "Type Electronics", "Filter by price"],
            expected_result="Matching products listed accurately.",
            priority="Medium",
            requirement_ids=[],  # Unmapped explicitly
        )
    ]

    checker = CoverageChecker(semantic_threshold=0.60)
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 100.0
    assert "REQ-201" in res.covered_requirements
    assert "TC201" in res.mapping["REQ-201"]


def test_mixed_mapping():
    """Tests hybrid coverage combining explicit and semantic mapping."""
    reqs = [
        Requirement(id="REQ-001", requirement="User login with valid credentials."),
        Requirement(id="REQ-002", requirement="Password reset link sent to registered email address."),
    ]

    tcs = [
        # Explicitly mapped to REQ-001
        TestCase(
            id="TC001",
            title="Login Test",
            description="User login test",
            steps=["Step 1"],
            expected_result="Result",
            requirement_ids=["REQ-001"],
        ),
        # Unmapped explicitly, but semantically matches REQ-002
        TestCase(
            id="TC002",
            title="Password Reset Email Test",
            description="Verify password reset link is sent to user registered email address.",
            steps=["Click forgot password", "Submit email"],
            expected_result="Reset email sent.",
            requirement_ids=[],
        ),
    ]

    checker = CoverageChecker(semantic_threshold=0.60)
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 100.0
    assert "TC001" in res.mapping["REQ-001"]
    assert "TC002" in res.mapping["REQ-002"]


def test_multiple_mappings():
    """Tests multiple test cases mapping to one requirement and one test case mapping to multiple requirements."""
    reqs = [
        Requirement(id="REQ-001", requirement="Customer can login."),
        Requirement(id="REQ-002", requirement="System locks user account after 5 failed login attempts."),
    ]

    tcs = [
        # One testcase covering BOTH REQ-001 and REQ-002
        TestCase(
            id="TC001",
            title="Login and Lockout Integration Test",
            description="Verify login and account lockout",
            steps=["Step 1"],
            expected_result="Result",
            requirement_ids=["REQ-001", "REQ-002"],
        ),
        # Second testcase also covering REQ-001
        TestCase(
            id="TC002",
            title="Secondary Login Verification",
            description="Verify valid login",
            steps=["Step 1"],
            expected_result="Result",
            requirement_ids=["REQ-001"],
        ),
    ]

    checker = CoverageChecker()
    res = checker.check_coverage(reqs, tcs)

    assert res.coverage_percentage == 100.0
    # REQ-001 covered by TC001 and TC002
    assert "TC001" in res.mapping["REQ-001"]
    assert "TC002" in res.mapping["REQ-001"]
    # REQ-002 covered by TC001
    assert "TC001" in res.mapping["REQ-002"]


def test_empty_input():
    """Tests empty requirements list handling."""
    checker = CoverageChecker()
    res = checker.check_coverage([], [])

    assert res.total_requirements == 0
    assert res.coverage_percentage == 0.0
    assert res.missing_requirements == []


def test_invalid_inputs():
    """Tests that invalid parameter types raise CoverageCheckError."""
    checker = CoverageChecker()

    with pytest.raises(CoverageCheckError) as exc1:
        checker.check_coverage("invalid_reqs", [])  # type: ignore

    assert "Invalid requirement list" in str(exc1.value)

    with pytest.raises(CoverageCheckError) as exc2:
        checker.check_coverage([], "invalid_tcs")  # type: ignore

    assert "Invalid testcase list" in str(exc2.value)

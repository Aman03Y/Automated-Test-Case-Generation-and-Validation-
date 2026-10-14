"""
Unit Tests for AI Semantic Duplicate Detector Service (Module 3).
"""

import pytest
from models.testcase import TestCase
from models.validation_result import DuplicateMatch
from services.duplicate_detector import DuplicateDetector
from utils.exceptions import DuplicateDetectionError


def test_similar_testcases():
    """Tests that highly similar test cases are detected as duplicates."""
    detector = DuplicateDetector(similarity_threshold=0.85)

    tc1 = TestCase(
        id="TC001",
        title="User Login Test",
        description="Verify user login with valid username and password credentials.",
        steps=["Open login page", "Type username and password", "Click Login"],
        expected_result="User dashboard is displayed successfully.",
        priority="High",
    )

    tc2 = TestCase(
        id="TC002",
        title="User Login Verification Test",
        description="Verify user login with valid username and password credentials.",
        steps=["Open login page", "Type username and password", "Click Login button"],
        expected_result="User dashboard is displayed successfully.",
        priority="High",
    )

    matches = detector.detect_duplicates([tc1, tc2])

    assert len(matches) == 1
    match = matches[0]
    assert match.testcase_1 == "TC001"
    assert match.testcase_2 == "TC002"
    assert match.duplicate is True
    assert match.similarity >= 0.85


def test_different_testcases():
    """Tests that distinct test cases are not flagged as duplicates."""
    detector = DuplicateDetector(similarity_threshold=0.85)

    tc1 = TestCase(
        id="TC001",
        title="User Login Test",
        description="Verify user login with valid credentials.",
        steps=["Open login page", "Enter credentials", "Submit"],
        expected_result="User dashboard displayed.",
        priority="High",
    )

    tc2 = TestCase(
        id="TC002",
        title="Product Search Test",
        description="Verify product search functionality by category.",
        steps=["Open search bar", "Type Electronics", "Filter by price"],
        expected_result="Matching products listed.",
        priority="Low",
    )

    matches = detector.detect_duplicates([tc1, tc2])

    assert len(matches) == 1
    match = matches[0]
    assert match.duplicate is False
    assert match.similarity < 0.85


def test_threshold_behavior():
    """Tests configurable threshold behavior (0.50 vs 0.98)."""
    tc1 = TestCase(
        id="TC001",
        title="Password Reset Request",
        description="Verify user can request password reset link.",
        steps=["Click forgot password", "Enter email"],
        expected_result="Reset email sent.",
        priority="High",
    )

    tc2 = TestCase(
        id="TC002",
        title="Password Reset Email Delivery",
        description="Verify user receives password reset email in inbox.",
        steps=["Open email client", "Check inbox"],
        expected_result="Email received.",
        priority="High",
    )

    # Moderate similarity test
    detector_low = DuplicateDetector(similarity_threshold=0.40)
    matches_low = detector_low.detect_duplicates([tc1, tc2])

    detector_high = DuplicateDetector(similarity_threshold=0.98)
    matches_high = detector_high.detect_duplicates([tc1, tc2])

    assert matches_low[0].duplicate is True
    assert matches_high[0].duplicate is False


def test_empty_testcase_list():
    """Tests that an empty testcase list returns empty matches list."""
    detector = DuplicateDetector()
    matches = detector.detect_duplicates([])

    assert matches == []


def test_single_testcase():
    """Tests that a single testcase list returns empty matches list."""
    detector = DuplicateDetector()
    tc1 = TestCase(
        id="TC001",
        title="Single Test",
        description="Single description",
        steps=["Step 1"],
        expected_result="Result",
        priority="Medium",
    )
    matches = detector.detect_duplicates([tc1])

    assert matches == []


def test_large_dataset_performance():
    """Tests duplicate detection across a larger dataset (50 test cases) verifying caching performance."""
    detector = DuplicateDetector(similarity_threshold=0.85)

    testcases = []
    # Create 40 distinct test cases
    for i in range(1, 41):
        tc = TestCase(
            id=f"TC{i:03d}",
            title=f"Functional Test Scenario {i}",
            description=f"Description for unique test scenario number {i}.",
            steps=[f"Step 1 for test {i}", f"Step 2 for test {i}"],
            expected_result=f"Expected result outcome {i}",
            priority="Medium",
        )
        testcases.append(tc)

    # Add 10 near-duplicate test cases
    for i in range(1, 11):
        dup_tc = TestCase(
            id=f"TC_DUP_{i:03d}",
            title=f"Functional Test Scenario {i}",
            description=f"Description for unique test scenario number {i}.",
            steps=[f"Step 1 for test {i}", f"Step 2 for test {i}"],
            expected_result=f"Expected result outcome {i}",
            priority="Medium",
        )
        testcases.append(dup_tc)

    # First run (computes and caches embeddings)
    matches_run1 = detector.detect_duplicates(testcases)
    assert len(matches_run1) == (50 * 49) // 2  # Total pairwise combinations

    # Second run (retrieves embeddings from cache)
    matches_run2 = detector.detect_duplicates(testcases)
    assert len(matches_run2) == len(matches_run1)


def test_invalid_input_type():
    """Tests that passing invalid input type raises DuplicateDetectionError."""
    detector = DuplicateDetector()
    with pytest.raises(DuplicateDetectionError) as exc_info:
        detector.detect_duplicates("not_a_list")  # type: ignore

    assert "Invalid testcase list" in str(exc_info.value)

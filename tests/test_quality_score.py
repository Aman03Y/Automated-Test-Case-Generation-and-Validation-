"""
Unit Tests for Enterprise Project Quality Score Engine Service (Module 6).
"""

import pytest
from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import (
    CoverageResult,
    TestCaseValidationResult,
    ValidationStatus,
    DuplicateMatch,
)
from services.quality_score import QualityScoreCalculator


def test_excellent_project():
    """Tests quality score calculation for an Excellent Project (Grade A)."""
    cov_res = CoverageResult(
        total_requirements=4,
        covered_requirements_count=4,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001"]},
    )

    tcs = [
        TestCase(
            id=f"TC00{i}",
            title=f"Valid Test Scenario Title {i}",
            description=f"Detailed description for valid test scenario number {i}.",
            steps=["Step 1 execute", "Step 2 verify outcome"],
            expected_result=f"Expected result outcome for scenario {i}",
            priority="High",
            requirement_ids=[f"REQ-00{i}"],
        )
        for i in range(1, 5)
    ]

    val_results = [
        TestCaseValidationResult(
            testcase_id=tc.id,
            status=ValidationStatus.PASS,
            score=100,
            errors=[],
            warnings=[],
        )
        for tc in tcs
    ]

    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=cov_res,
        testcases=tcs,
        validation_results=val_results,
        duplicate_matches=[],
    )

    assert breakdown.overall_score >= 90.0
    assert "Grade A" in breakdown.grade
    assert breakdown.visual_summary == "Excellent"
    assert breakdown.coverage == 100.0
    assert breakdown.duplicate_rate == 0.0
    assert breakdown.average_testcase_score == 100.0
    assert breakdown.pass_count == 4
    assert breakdown.fail_count == 0


def test_average_project():
    """Tests quality score calculation for an Average Project (Grade B or C)."""
    cov_res = CoverageResult(
        total_requirements=4,
        covered_requirements_count=3,
        coverage_percentage=75.0,
        covered_requirements=["REQ-001", "REQ-002", "REQ-003"],
        missing_requirements=["REQ-004"],
        mapped_test_cases={"REQ-001": ["TC001"]},
    )

    tcs = [
        TestCase(
            id=f"TC00{i}",
            title=f"Test Title {i}",
            description=f"Description for scenario {i}.",
            steps=["Step 1"],
            expected_result=f"Outcome for scenario {i}",
            priority="Medium",
            requirement_ids=[f"REQ-00{i}"],
        )
        for i in range(1, 4)
    ]

    val_results = [
        TestCaseValidationResult(
            testcase_id="TC001", status=ValidationStatus.PASS, score=90, errors=[], warnings=[]
        ),
        TestCaseValidationResult(
            testcase_id="TC002", status=ValidationStatus.WARNING, score=75, errors=[], warnings=["Warning"]
        ),
        TestCaseValidationResult(
            testcase_id="TC003", status=ValidationStatus.PASS, score=85, errors=[], warnings=[]
        ),
    ]

    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=cov_res,
        testcases=tcs,
        validation_results=val_results,
        duplicate_matches=[],
    )

    assert 70.0 <= breakdown.overall_score < 90.0
    assert breakdown.grade in ["Grade B", "Grade C"]
    assert breakdown.visual_summary in ["Good", "Average"]


def test_poor_project():
    """Tests quality score calculation for a Poor / Critical Project (Grade D or F)."""
    cov_res = CoverageResult(
        total_requirements=10,
        covered_requirements_count=2,
        coverage_percentage=20.0,
        covered_requirements=["REQ-001", "REQ-002"],
        missing_requirements=[f"REQ-00{i}" for i in range(3, 11)],
        mapped_test_cases={},
    )

    tcs = [
        TestCase(
            id="TC001",
            title="Poor Test",
            description="Short",
            steps=["Step 1"],
            expected_result="OK",
            priority="High",
        )
    ]

    val_results = [
        TestCaseValidationResult(
            testcase_id="TC001",
            status=ValidationStatus.FAIL,
            score=30,
            errors=["Rule 2 Failed", "Rule 6 Failed"],
            warnings=[],
        )
    ]

    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=cov_res,
        testcases=tcs,
        validation_results=val_results,
        duplicate_matches=[],
    )

    assert breakdown.overall_score < 60.0
    assert "Grade F" in breakdown.grade
    assert breakdown.visual_summary == "Critical"
    assert breakdown.fail_count == 1


def test_no_coverage():
    """Tests quality score when requirement coverage is 0%."""
    cov_res = CoverageResult(
        total_requirements=5,
        covered_requirements_count=0,
        coverage_percentage=0.0,
        covered_requirements=[],
        missing_requirements=[f"REQ-00{i}" for i in range(1, 6)],
        mapped_test_cases={},
    )

    tcs = [
        TestCase(
            id="TC001",
            title="Valid Title Scenario",
            description="Detailed valid description for scenario",
            steps=["Step 1 execute"],
            expected_result="Expected outcome success",
            priority="High",
        )
    ]

    val_results = [
        TestCaseValidationResult(
            testcase_id="TC001", status=ValidationStatus.PASS, score=90, errors=[], warnings=[]
        )
    ]

    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=cov_res,
        testcases=tcs,
        validation_results=val_results,
        duplicate_matches=[],
    )

    # 35% coverage component is 0.0
    assert breakdown.score_breakdown["coverage"] == 0.0
    assert breakdown.coverage == 0.0


def test_100_percent_duplicates():
    """Tests quality score when 100% of test cases are duplicates."""
    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001", "TC002"]},
    )

    tcs = [
        TestCase(
            id="TC001",
            title="Login Test 1",
            description="User login scenario test description",
            steps=["Step 1"],
            expected_result="Dashboard appears",
            priority="High",
            requirement_ids=["REQ-001"],
        ),
        TestCase(
            id="TC002",
            title="Login Test 2",
            description="User login scenario test description",
            steps=["Step 1"],
            expected_result="Dashboard appears",
            priority="High",
            requirement_ids=["REQ-001"],
        ),
    ]

    dup_match = DuplicateMatch(
        tc1_id="TC001",
        tc2_id="TC002",
        similarity_score=0.95,
        similarity_percentage=95.0,
        is_duplicate=True,
    )

    val_results = [
        TestCaseValidationResult(
            testcase_id="TC001", status=ValidationStatus.WARNING, score=80, errors=[], warnings=["Duplicate"]
        ),
        TestCaseValidationResult(
            testcase_id="TC002", status=ValidationStatus.WARNING, score=80, errors=[], warnings=["Duplicate"]
        ),
    ]

    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=cov_res,
        testcases=tcs,
        validation_results=val_results,
        duplicate_matches=[dup_match],
    )

    assert breakdown.duplicate_rate == 100.0
    assert breakdown.score_breakdown["duplicate_penalty"] == 0.0


def test_empty_inputs():
    """Tests that empty inputs return overall score 0.0 and Grade F."""
    breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=None,
        testcases=[],
        validation_results=[],
        duplicate_matches=[],
    )

    assert breakdown.overall_score == 0.0
    assert breakdown.grade == "F"
    assert breakdown.visual_summary == "Critical"

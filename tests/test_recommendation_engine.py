"""
Unit Tests for AI Recommendation Engine Service (Module 6.5).
"""

import pytest
from models.validation_result import TestCaseValidationResult, ValidationStatus, CoverageResult
from models.report import QualityBreakdown
from services.recommendation_engine import RecommendationEngine


def test_missing_title_recommendation():
    """Tests recommendation generation for missing title."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.FAIL,
        score=60,
        errors=["Rule 1 Failed: Title is missing or empty."],
        warnings=[],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Provide a meaningful test case title." in rec["recommendations"]
    assert rec["priority"] in ["High", "Critical"]


def test_missing_description_recommendation():
    """Tests recommendation generation for missing description."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.FAIL,
        score=60,
        errors=["Rule 2 Failed: Description is missing or empty."],
        warnings=[],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Add a detailed description explaining the purpose of the test." in rec["recommendations"]


def test_short_description_recommendation():
    """Tests recommendation generation for short description."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.WARNING,
        score=85,
        errors=[],
        warnings=["Description is too short (min 15 characters required)."],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Expand the description with functional details." in rec["recommendations"]


def test_missing_steps_recommendation():
    """Tests recommendation generation for missing execution steps."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.FAIL,
        score=50,
        errors=["Rule 3 Failed: Test case must contain at least one step."],
        warnings=[],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Include detailed execution steps." in rec["recommendations"]


def test_poor_expected_result_recommendation():
    """Tests recommendation generation for vague expected result."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.WARNING,
        score=80,
        errors=[],
        warnings=["Expected result is too vague ('Success')."],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Expected result should describe observable system behaviour." in rec["recommendations"]


def test_duplicate_testcase_recommendation():
    """Tests recommendation generation for duplicate testcase."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.WARNING,
        score=75,
        errors=[],
        warnings=["Possible duplicate of TC004 (91% similarity)."],
        is_duplicate=True,
        duplicate_with=["TC004"],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "Merge this testcase with TC004 or remove the duplicate." in rec["recommendations"]


def test_requirement_not_covered_recommendation():
    """Tests project recommendation for missing requirement."""
    cov_res = CoverageResult(
        total_requirements=5,
        covered_requirements_count=4,
        coverage_percentage=80.0,
        covered_requirements=["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
        missing_requirements=["REQ-005"],
        mapped_test_cases={},
    )

    engine = RecommendationEngine()
    recs = engine.generate_uncovered_requirement_recommendations(cov_res)

    assert "Create at least one testcase covering REQ-005." in recs


def test_low_quality_score_recommendation():
    """Tests recommendation generation for low quality score (< 70)."""
    val_res = TestCaseValidationResult(
        testcase_id="TC001",
        status=ValidationStatus.FAIL,
        score=40,
        errors=["Rule 2 Failed", "Rule 3 Failed", "Rule 4 Failed"],
        warnings=[],
    )

    engine = RecommendationEngine()
    rec = engine.generate_single_testcase_recommendation(val_res)

    assert "This testcase requires major improvements before execution." in rec["recommendations"]


def test_project_level_recommendations():
    """Tests project-level recommendation generation (coverage, duplicate rate, average score)."""
    cov_res = CoverageResult(
        total_requirements=10,
        covered_requirements_count=7,
        coverage_percentage=70.0,  # Below 80%
        covered_requirements=[],
        missing_requirements=["REQ-008", "REQ-009", "REQ-010"],
        mapped_test_cases={},
    )

    qb = QualityBreakdown(
        overall_score=72.0,
        grade="Grade C",
        coverage=70.0,
        duplicate_rate=15.0,  # Above 10%
        average_testcase_score=68.0,  # Below 75
        pass_count=5,
        warning_count=3,
        fail_count=2,
    )

    engine = RecommendationEngine()
    proj_recs = engine.generate_project_recommendations(cov_res, qb)

    assert "Increase testcase coverage." in proj_recs
    assert "Review duplicate testcases." in proj_recs
    assert "Improve testcase documentation quality." in proj_recs

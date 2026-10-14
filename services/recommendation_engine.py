"""
AI Recommendation Engine Service.

Module 6.5: AI Recommendation Engine
Analyzes validation outcomes, requirement coverage, duplicates, and project quality breakdown
to automatically generate actionable recommendations for test cases and the overall project.
"""

import time
from typing import List, Dict, Any, Optional
from models.validation_result import TestCaseValidationResult, CoverageResult, DuplicateMatch
from models.report import QualityBreakdown
from utils.logger import get_logger

logger = get_logger("RecommendationEngine")


class RecommendationEngine:
    """Production-grade Rule-Based Intelligent Recommendation Generator for Software Test Cases."""

    def __init__(
        self,
        min_quality_score_threshold: int = 70,
        low_coverage_threshold: float = 80.0,
        high_duplicate_rate_threshold: float = 10.0,
        low_avg_score_threshold: float = 75.0,
    ):
        """Initializes RecommendationEngine.

        Args:
            min_quality_score_threshold: Threshold below which test cases require major improvements.
            low_coverage_threshold: Coverage threshold (%) triggering coverage increase recommendation.
            high_duplicate_rate_threshold: Duplicate rate threshold (%) triggering duplicate review.
            low_avg_score_threshold: Average score threshold triggering quality improvement.
        """
        self.min_quality_score_threshold = min_quality_score_threshold
        self.low_coverage_threshold = low_coverage_threshold
        self.high_duplicate_rate_threshold = high_duplicate_rate_threshold
        self.low_avg_score_threshold = low_avg_score_threshold

    def generate_recommendations(
        self,
        validation_results: List[TestCaseValidationResult],
        coverage_result: Optional[CoverageResult] = None,
        duplicate_matches: Optional[List[DuplicateMatch]] = None,
        quality_breakdown: Optional[QualityBreakdown] = None,
    ) -> Dict[str, Any]:
        """Generates comprehensive test case recommendations and project-level recommendations.

        Args:
            validation_results: Output list of TestCaseValidationResult from Module 5.
            coverage_result: CoverageResult output from Module 4.
            duplicate_matches: List of DuplicateMatch from Module 3.
            quality_breakdown: QualityBreakdown from Module 6.

        Returns:
            Dictionary containing:
              - testcase_recommendations: List of test case recommendation dicts.
              - project_recommendations: List of project-level recommendation strings.
              - uncovered_requirement_recommendations: List of missing requirement recommendations.
        """
        start_time = time.perf_counter()
        logger.info("Recommendation Engine started: Analyzing validation outputs...")

        tc_recs: List[Dict[str, Any]] = []
        for val_res in validation_results:
            rec_obj = self.generate_single_testcase_recommendation(val_res)
            if rec_obj["recommendations"]:
                tc_recs.append(rec_obj)

        proj_recs = self.generate_project_recommendations(coverage_result, quality_breakdown)
        uncovered_recs = self.generate_uncovered_requirement_recommendations(coverage_result)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Recommendation Engine finished in {elapsed_ms:.2f} ms: "
            f"Generated recommendations for {len(tc_recs)} test cases, "
            f"{len(proj_recs)} project guidelines, and {len(uncovered_recs)} missing requirement actions."
        )

        return {
            "testcase_recommendations": tc_recs,
            "project_recommendations": proj_recs,
            "uncovered_requirement_recommendations": uncovered_recs,
        }

    def generate_single_testcase_recommendation(
        self, val_result: TestCaseValidationResult
    ) -> Dict[str, Any]:
        """Evaluates rules for a single test case to produce actionable recommendations.

        Args:
            val_result: TestCaseValidationResult instance.

        Returns:
            Dictionary matching format:
            {
              "testcase_id": "TC001",
              "recommendations": ["..."],
              "priority": "High"
            }
        """
        recs: List[str] = []
        has_error = False

        errors = val_result.errors or []
        warnings = val_result.warnings or []

        # Rule Checks on Errors
        for err in errors:
            err_str = str(err).lower()
            if "title" in err_str:
                recs.append("Provide a meaningful test case title.")
                has_error = True
            elif "description is missing" in err_str or "description" in err_str:
                recs.append("Add a detailed description explaining the purpose of the test.")
                has_error = True
            elif "step" in err_str:
                recs.append("Include detailed execution steps.")
                has_error = True
            elif "expected result is missing" in err_str:
                recs.append("Provide a clear and observable expected result.")
                has_error = True
            elif "requirement mapping" in err_str or "unmapped" in err_str:
                recs.append("Map this testcase to an appropriate software requirement.")
                has_error = True

        # Rule Checks on Warnings
        for warn in warnings:
            warn_str = str(warn).lower()
            if "description is too short" in warn_str:
                recs.append("Expand the description with functional details.")
            elif "vague" in warn_str:
                recs.append("Expected result should describe observable system behaviour.")
            elif "duplicate" in warn_str:
                pass  # Handled below via duplicate_with list

        # Duplicate Testcase Recommendation
        if val_result.is_duplicate and val_result.duplicate_with:
            for dup_id in val_result.duplicate_with:
                rec_msg = f"Merge this testcase with {dup_id} or remove the duplicate."
                if rec_msg not in recs:
                    recs.append(rec_msg)

        # Low Quality Score Recommendation (< 70)
        if val_result.score < self.min_quality_score_threshold:
            rec_low = "This testcase requires major improvements before execution."
            if rec_low not in recs:
                recs.append(rec_low)

        # Priority Determination
        if has_error or val_result.score < 60:
            priority = "Critical" if val_result.score < 50 else "High"
        elif val_result.score < 80 or len(warnings) > 0 or val_result.is_duplicate:
            priority = "High" if val_result.is_duplicate else "Medium"
        else:
            priority = "Low"

        return {
            "testcase_id": val_result.testcase_id,
            "recommendations": recs,
            "priority": priority,
        }

    def generate_project_recommendations(
        self,
        coverage_result: Optional[CoverageResult],
        quality_breakdown: Optional[QualityBreakdown],
    ) -> List[str]:
        """Generates project-level recommendations based on overall metric thresholds.

        Args:
            coverage_result: CoverageResult instance.
            quality_breakdown: QualityBreakdown instance.

        Returns:
            List of project-level recommendation strings.
        """
        proj_recs: List[str] = []

        if coverage_result:
            if coverage_result.coverage_percentage < self.low_coverage_threshold:
                proj_recs.append("Increase testcase coverage.")

        if quality_breakdown:
            if quality_breakdown.duplicate_rate > self.high_duplicate_rate_threshold:
                proj_recs.append("Review duplicate testcases.")

            if quality_breakdown.average_testcase_score < self.low_avg_score_threshold:
                proj_recs.append("Improve testcase documentation quality.")

        return proj_recs

    def generate_uncovered_requirement_recommendations(
        self, coverage_result: Optional[CoverageResult]
    ) -> List[str]:
        """Generates specific recommendations for each missing requirement.

        Args:
            coverage_result: CoverageResult instance.

        Returns:
            List of missing requirement recommendation strings.
        """
        uncovered_recs: List[str] = []
        if coverage_result and coverage_result.missing_requirements:
            for req_id in coverage_result.missing_requirements:
                uncovered_recs.append(f"Create at least one testcase covering {req_id}.")
        return uncovered_recs

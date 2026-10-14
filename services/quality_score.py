"""
Enterprise Project Quality Score Engine Service.

Module 6: Project Quality Score Engine
Calculates an enterprise-grade weighted quality score (0 to 100) using:
  - Requirement Coverage (35%)
  - Average Test Case Score (35%)
  - Duplicate Penalty (20%)
  - Formatting Quality (10%)
Assigns letter grades (A, B, C, D, F) and visual summary descriptors.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from models.report import QualityBreakdown
from models.testcase import TestCase, PriorityLevel
from models.validation_result import CoverageResult, TestCaseValidationResult, DuplicateMatch, ValidationStatus
from utils.logger import get_logger

logger = get_logger("QualityScore")


class QualityScoreCalculator:
    """Enterprise Quality Scoring Engine for Software Test Suites."""

    @staticmethod
    def calculate_score(
        coverage_result: Optional[CoverageResult],
        testcases: Optional[List[TestCase]],
        validation_results: Optional[List[TestCaseValidationResult]],
        duplicate_matches: Optional[List[DuplicateMatch]],
    ) -> QualityBreakdown:
        """Calculates enterprise weighted quality metrics, component scores, grade, and visual summary.

        Weighted Components:
          - Requirement Coverage : 35%
          - Average Quality Score: 35%
          - Duplicate Penalty    : 20%
          - Formatting Quality   : 10%

        Grades:
          - 90-100: Grade A (Excellent)
          - 80-89 : Grade B (Good)
          - 70-79 : Grade C (Average)
          - 60-69 : Grade D (Poor)
          - < 60  : Grade F (Critical)

        Args:
            coverage_result: CoverageResult output from Module 4.
            testcases: List of TestCase models loaded from Module 2.
            validation_results: List of TestCaseValidationResult outputs from Module 5.
            duplicate_matches: List of DuplicateMatch outputs from Module 3.

        Returns:
            QualityBreakdown object matching target schema.
        """
        start_time = time.perf_counter()

        tcs = testcases or []
        val_res = validation_results or []
        dup_matches = duplicate_matches or []

        total_tcs = len(tcs)

        # Handle empty inputs gracefully
        if total_tcs == 0 or coverage_result is None:
            logger.warning("Empty or missing inputs provided to QualityScoreCalculator. Returning Grade F.")
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return QualityBreakdown(
                overall_score=0.0,
                grade="F",
                coverage=0.0,
                duplicate_rate=0.0,
                average_testcase_score=0.0,
                pass_count=0,
                warning_count=0,
                fail_count=0,
                score_breakdown={
                    "coverage": 0.0,
                    "average_quality": 0.0,
                    "duplicate_penalty": 0.0,
                    "formatting": 0.0,
                },
                visual_summary="Critical",
            )

        # 1. Requirement Coverage Component (35%)
        coverage_pct = max(0.0, min(100.0, coverage_result.coverage_percentage))
        coverage_component = (coverage_pct / 100.0) * 35.0

        # 2. Average Test Case Score Component (35%)
        tc_scores = [vr.score for vr in val_res] if val_res else [0.0]
        avg_tc_score = sum(tc_scores) / len(tc_scores) if tc_scores else 0.0
        avg_quality_component = (avg_tc_score / 100.0) * 35.0

        # 3. Duplicate Penalty Component (20%)
        duplicate_tc_ids = set()
        for dm in dup_matches:
            if dm.is_duplicate or dm.duplicate:
                duplicate_tc_ids.add(dm.tc1_id)
                duplicate_tc_ids.add(dm.tc2_id)

        duplicate_tc_count = min(total_tcs, len(duplicate_tc_ids))
        duplicate_rate = (duplicate_tc_count / total_tcs * 100.0) if total_tcs > 0 else 0.0
        non_duplicate_ratio = max(0.0, 1.0 - (duplicate_tc_count / total_tcs))
        duplicate_penalty_component = non_duplicate_ratio * 20.0

        # 4. Formatting Quality Component (10%)
        formatting_pass_count = 0
        for tc in tcs:
            is_well_formatted = True
            if not PriorityLevel.is_valid(tc.priority):
                is_well_formatted = False
            if len(tc.steps) < 1 or any(len(str(s).strip()) < 3 for s in tc.steps):
                is_well_formatted = False
            if len(tc.expected_result.strip()) < 6:
                is_well_formatted = False
            if len(tc.description.strip()) < 10:
                is_well_formatted = False

            if is_well_formatted:
                formatting_pass_count += 1

        formatting_ratio = formatting_pass_count / total_tcs if total_tcs > 0 else 0.0
        formatting_component = formatting_ratio * 10.0

        # Final Overall Score Sum
        overall_score = coverage_component + avg_quality_component + duplicate_penalty_component + formatting_component
        overall_score = round(max(0.0, min(100.0, overall_score)), 2)

        # Grade & Visual Summary Mapping
        grade, visual_summary = QualityScoreCalculator._determine_grade_and_summary(overall_score)

        # Counts
        pass_count = sum(1 for v in val_res if v.status == ValidationStatus.PASS or v.status.value == "PASS")
        warning_count = sum(1 for v in val_res if v.status == ValidationStatus.WARNING or v.status.value == "WARNING")
        fail_count = sum(1 for v in val_res if v.status == ValidationStatus.FAIL or v.status.value == "FAIL")

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            f"Quality Score Calculation Completed in {elapsed_ms:.2f} ms: "
            f"Overall={overall_score}/100, Grade={grade} ({visual_summary}) | "
            f"Coverage={coverage_pct:.1f}%, AvgScore={avg_tc_score:.1f}, DupRate={duplicate_rate:.1f}%."
        )

        return QualityBreakdown(
            overall_score=overall_score,
            grade=grade,
            coverage=round(coverage_pct, 2),
            duplicate_rate=round(duplicate_rate, 2),
            average_testcase_score=round(avg_tc_score, 2),
            pass_count=pass_count,
            warning_count=warning_count,
            fail_count=fail_count,
            score_breakdown={
                "coverage": round(coverage_component, 2),
                "average_quality": round(avg_quality_component, 2),
                "duplicate_penalty": round(duplicate_penalty_component, 2),
                "formatting": round(formatting_component, 2),
            },
            visual_summary=visual_summary,
        )

    @staticmethod
    def _determine_grade_and_summary(score: float) -> Tuple[str, str]:
        """Determines Letter Grade (A, B, C, D, F) and Visual Summary descriptor based on score.

        Args:
            score: Overall score float (0.0 to 100.0).

        Returns:
            Tuple of (Grade string, Visual Summary string).
        """
        if score >= 90.0:
            return ("Grade A", "Excellent")
        elif score >= 80.0:
            return ("Grade B", "Good")
        elif score >= 70.0:
            return ("Grade C", "Average")
        elif score >= 60.0:
            return ("Grade D", "Poor")
        else:
            return ("Grade F", "Critical")

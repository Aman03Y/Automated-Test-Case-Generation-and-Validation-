"""
AI Validation Engine Service.

Module 5: AI Validation Engine
Combines 9 rule checks (Title, Description, Steps, Expected Result, Priority,
Requirement Mapping, Duplicate Detection, Description Quality, Expected Result Quality),
calculates individual test case validation scores (0 to 100), and assigns PASS, WARNING, or FAIL status.
"""

import time
from typing import List, Dict, Set, Any, Optional
from models.requirement import Requirement
from models.testcase import TestCase, PriorityLevel
from models.validation_result import (
    TestCaseValidationResult,
    ValidationStatus,
    DuplicateMatch,
    CoverageResult,
)
from utils.exceptions import ValidationError
from utils.logger import get_logger

logger = get_logger("ValidationEngine")

VAGUE_EXPECTED_RESULTS: Set[str] = {
    "success",
    "works",
    "done",
    "ok",
    "pass",
    "successful",
    "testing",
    "fine",
    "good",
    "passed",
    "test pass",
    "no error",
}


class ValidationEngine:
    """Production-ready AI Test Case Validation Engine combining rule checks, duplicates, and coverage."""

    def __init__(
        self,
        min_description_length: int = 15,
        min_expected_result_length: int = 6,
        valid_req_ids: Optional[List[str]] = None,
    ):
        """Initializes ValidationEngine.

        Args:
            min_description_length: Minimum character length for valid descriptions.
            min_expected_result_length: Minimum character length for detailed expected results.
            valid_req_ids: Optional list of valid requirement IDs.
        """
        self.min_description_length = min_description_length
        self.min_expected_result_length = min_expected_result_length
        self.valid_req_ids: Set[str] = set(valid_req_ids) if valid_req_ids else set()

    def validate_testcases(
        self,
        testcases: List[TestCase],
        requirements: Optional[List[Requirement]] = None,
        duplicate_results: Optional[List[DuplicateMatch]] = None,
        coverage_results: Optional[CoverageResult] = None,
        duplicate_matches: Optional[List[DuplicateMatch]] = None,
    ) -> List[TestCaseValidationResult]:
        """Evaluates rules across all test cases using outputs from previous modules.

        Args:
            testcases: List of TestCase models.
            requirements: Optional list of Requirement models.
            duplicate_results: Optional list of DuplicateMatch outputs from Module 3.
            coverage_results: Optional CoverageResult output from Module 4.
            duplicate_matches: Optional list of DuplicateMatch outputs.

        Returns:
            List of TestCaseValidationResult objects containing score, status, errors, and warnings.
        """
        start_time = time.perf_counter()
        logger.info(f"Validation Engine started: Evaluating {len(testcases)} test cases...")

        if requirements:
            self.valid_req_ids.update(req.id for req in requirements)

        # Build requirement mapping set from coverage results
        covered_req_tc_map: Dict[str, Set[str]] = {}
        if coverage_results:
            mapping = coverage_results.mapped_test_cases or coverage_results.mapping
            for req_id, tc_list in mapping.items():
                self.valid_req_ids.add(req_id)
                for tc_id in tc_list:
                    covered_req_tc_map.setdefault(tc_id, set()).add(req_id)

        duplicate_map: Dict[str, List[Dict[str, Any]]] = {}
        dup_list = duplicate_results if duplicate_results is not None else duplicate_matches
        if dup_list:
            for match in dup_list:
                if match.is_duplicate or match.duplicate:
                    match_dict_1 = {
                        "other_tc_id": match.tc2_id,
                        "similarity_percentage": round(match.similarity_percentage, 1),
                        "similarity_score": round(match.similarity_score, 4),
                    }
                    duplicate_map.setdefault(match.tc1_id, []).append(match_dict_1)

                    match_dict_2 = {
                        "other_tc_id": match.tc1_id,
                        "similarity_percentage": round(match.similarity_percentage, 1),
                        "similarity_score": round(match.similarity_score, 4),
                    }
                    duplicate_map.setdefault(match.tc2_id, []).append(match_dict_2)

        results: List[TestCaseValidationResult] = []

        for tc in testcases:
            tc_dups = duplicate_map.get(tc.id, [])
            mapped_reqs = covered_req_tc_map.get(tc.id, set())
            result = self.validate_single_testcase(tc, duplicate_matches=tc_dups, mapped_reqs=mapped_reqs)
            results.append(result)

        pass_count = sum(1 for r in results if r.status == ValidationStatus.PASS)
        warn_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        fail_count = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Validation Engine finished in {elapsed_ms:.2f} ms: "
            f"PASS={pass_count}, WARNING={warn_count}, FAIL={fail_count} | "
            f"Total Errors={total_errors}, Total Warnings={total_warnings}."
        )

        return results

    def validate_single_testcase(
        self,
        tc: TestCase,
        duplicate_matches: Optional[List[Dict[str, Any]]] = None,
        mapped_reqs: Optional[Set[str]] = None,
    ) -> TestCaseValidationResult:
        """Validates a single test case against all 9 rules and calculates validation score (0-100).

        Args:
            tc: TestCase model instance.
            duplicate_matches: Duplicate match info list for this testcase.
            mapped_reqs: Set of requirement IDs mapped to this testcase.

        Returns:
            TestCaseValidationResult instance.
        """
        errors: List[str] = []
        warnings: List[str] = []
        dups = duplicate_matches or []
        req_set = mapped_reqs or set()

        score = 100

        # Rule 1: Title Exists
        if not tc.title or not tc.title.strip():
            errors.append("Rule 1 Failed: Title is missing or empty.")
            score -= 20

        # Rule 2: Description Exists
        if not tc.description or not tc.description.strip():
            errors.append("Rule 2 Failed: Description is missing or empty.")
            score -= 20
        else:
            # Rule 8: Description Quality (Length)
            if len(tc.description.strip()) < self.min_description_length:
                warnings.append(
                    f"Description is too short (min {self.min_description_length} characters required)."
                )
                score -= 8

        # Rule 3: Steps Present
        if not tc.steps or len(tc.steps) == 0:
            errors.append("Rule 3 Failed: Test case must contain at least one step.")
            score -= 20
        else:
            empty_steps = [idx for idx, s in enumerate(tc.steps) if not s or not str(s).strip()]
            if empty_steps:
                warnings.append(f"Contains empty execution steps at index: {empty_steps}")
                score -= 5

        # Rule 4 & 9: Expected Result Exists and Quality
        if not tc.expected_result or not tc.expected_result.strip():
            errors.append("Rule 4 Failed: Expected result is missing or empty.")
            score -= 20
        else:
            exp_clean = tc.expected_result.strip().lower()
            if exp_clean in VAGUE_EXPECTED_RESULTS or len(exp_clean) < self.min_expected_result_length:
                warnings.append(f"Expected result is too vague ('{tc.expected_result.strip()}').")
                score -= 8

        # Rule 5: Priority Valid
        if not tc.priority or not tc.priority.strip():
            errors.append("Rule 5 Failed: Priority field is missing.")
            score -= 20
        elif not PriorityLevel.is_valid(tc.priority):
            errors.append(
                f"Rule 5 Failed: Priority '{tc.priority}' is invalid. Expected one of Critical, High, Medium, Low."
            )
            score -= 20

        # Rule 6: Requirement Mapping
        tc_req_ids = set(tc.requirement_ids)
        if tc.requirement_id:
            tc_req_ids.add(tc.requirement_id)
        all_mapped_reqs = tc_req_ids.union(req_set)

        if not all_mapped_reqs:
            errors.append("Rule 6 Failed: Requirement mapping missing (test case is not mapped to any requirement).")
            score -= 20
        elif self.valid_req_ids and not any(r in self.valid_req_ids for r in all_mapped_reqs):
            warnings.append(
                f"Warning: Mapped requirement ID(s) '{list(all_mapped_reqs)}' not found in workspace requirements specifications."
            )
            score -= 8

        # Rule 7: Duplicate Detection Check
        is_duplicate = False
        dup_tc_ids: List[str] = []
        if dups:
            is_duplicate = True
            for d in dups:
                other_id = d.get("other_tc_id", "")
                sim_pct = d.get("similarity_percentage", 0.0)
                dup_tc_ids.append(other_id)
                warnings.append(f"Possible duplicate of {other_id} ({sim_pct:.0f}% similarity).")
                score -= 10

        # Bound Score 0 to 100
        final_score = int(max(0, min(100, score)))

        # Determine Status
        if errors:
            status = ValidationStatus.FAIL
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASS

        primary_req_id = list(all_mapped_reqs)[0] if all_mapped_reqs else None

        return TestCaseValidationResult(
            testcase_id=tc.id,
            status=status,
            score=final_score,
            errors=errors,
            warnings=warnings,
            mapped_requirement_id=primary_req_id,
            is_duplicate=is_duplicate,
            duplicate_with=dup_tc_ids,
            duplicate_matches=dups,
        )

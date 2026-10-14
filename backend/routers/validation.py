import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.config import settings
from backend.dependencies import AppState, get_app_state
from backend.schemas.api_schemas import (
    AutoFixResponse,
    AutoFixSummary,
    ValidationPipelineRequest,
)
from models.requirement import Requirement
from models.testcase import PriorityLevel, TestCase
from services.coverage_checker import CoverageChecker
from services.duplicate_detector import DuplicateDetector
from services.parser import RequirementParser
from services.quality_score import QualityScoreCalculator
from services.report_generator import ReportGenerator
from services.testcase_loader import TestCaseLoader
from services.traceability_matrix import TraceabilityMatrixGenerator
from services.validator import ValidationEngine
from utils.logger import get_logger

logger = get_logger("API_Validation")
router = APIRouter(prefix="/api", tags=["Validation"])

VALID_SRS_CATALOG = {
    "REQ-01",
    "REQ-02",
    "REQ-03",
    "REQ-04",
    "REQ-05",
    "REQ-001",
    "REQ-002",
    "REQ-003",
    "REQ-004",
    "REQ-005",
}


@router.post("/validate", summary="Run full AI testcase validation pipeline")
async def run_validation(
    payload: Optional[ValidationPipelineRequest] = None,
    app_state: AppState = Depends(get_app_state),
):
    """Executes the full automated validation pipeline against uploaded requirements and test cases."""
    sim_threshold = payload.similarity_threshold if payload else 0.85
    requirements = (
        payload.requirements
        if (payload and payload.requirements)
        else app_state.requirements
    )
    testcases = (
        payload.testcases if (payload and payload.testcases) else app_state.testcases
    )

    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No requirements uploaded. Please upload requirements first via /api/requirements/upload.",
        )
    if not testcases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No test cases uploaded. Please upload test cases first via /api/testcases/upload.",
        )

    # 1. Duplicate Detection
    detector = DuplicateDetector(similarity_threshold=sim_threshold)
    duplicate_matches = detector.detect_duplicates(testcases)

    # 2. Coverage Checking
    coverage_checker = CoverageChecker()
    coverage_result = coverage_checker.check_coverage(requirements, testcases)

    # 3. Rule Validation
    valid_req_ids = [req.id for req in requirements]
    validator = ValidationEngine(valid_req_ids=valid_req_ids)
    validation_results = validator.validate_testcases(
        testcases, duplicate_matches=duplicate_matches
    )

    # 4. Quality Score
    quality_breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=coverage_result,
        testcases=testcases,
        validation_results=validation_results,
        duplicate_matches=duplicate_matches,
    )

    # 5. Requirement Traceability Matrix (RTM)
    rtm_gen = TraceabilityMatrixGenerator(output_dir=settings.output_dir)
    rtm_data = rtm_gen.generate_rtm(
        coverage_result=coverage_result,
        requirements=requirements,
        testcases=testcases,
    )
    app_state.last_rtm = rtm_data

    # 6. Report Generation
    report_gen = ReportGenerator(output_dir=settings.output_dir)
    report = report_gen.generate_report(
        requirements=requirements,
        testcases=testcases,
        duplicate_matches=duplicate_matches,
        coverage_result=coverage_result,
        validation_results=validation_results,
        quality_breakdown=quality_breakdown,
    )
    app_state.last_report = report
    return report.to_dict()


@router.post("/testcases/validate-tests", response_model=AutoFixResponse)
async def validate_tests(file: UploadFile = File(...)):
    """Validates, deduplicates, and sanitizes test cases uploaded in JSON format."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        content = await file.read()
        raw_tcs = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")

    report_log = []

    # 1. Structural Sanitization & Loading
    loader = TestCaseLoader(strict=False)
    tcs = loader.validate_testcases(raw_tcs)

    for i, tc in enumerate(tcs):
        # Auto-generate missing IDs
        if not tc.id or tc.id.startswith("TC-EXT-") or tc.id.strip() == "":
            tc.id = f"TC-{str(uuid.uuid4())[:6].upper()}"
            report_log.append(f"[CLEANED] Auto-generated ID for test case: {tc.id}")

        # Enforce enum priorities
        if not tc.priority or not PriorityLevel.is_valid(tc.priority):
            tc.priority = "Medium"
            report_log.append(f"[CLEANED] Forced valid priority for {tc.id}")

        # Ensure steps are string arrays
        if not tc.steps or not isinstance(tc.steps, list):
            tc.steps = ["Execute step 1"]
            report_log.append(f"[CLEANED] Forced steps array for {tc.id}")

    # 2. Master SRS Validation
    for tc in tcs:
        valid_reqs = []
        original_reqs = list(tc.requirement_ids)
        for req in original_reqs:
            req_clean = str(req).strip()
            if req_clean in VALID_SRS_CATALOG:
                valid_reqs.append(req_clean)

        if not valid_reqs:
            tc.requirement_ids = ["ORPHAN-UNMAPPED"]
            report_log.append(
                f"[ORPHAN_FLAG] {tc.id} had invalid/no requirements. Tagged as ORPHAN-UNMAPPED."
            )
        else:
            tc.requirement_ids = valid_reqs
            if len(valid_reqs) < len(original_reqs):
                report_log.append(
                    f"[CLEANED] {tc.id} had invalid requirement IDs stripped."
                )

    # 3. Exact Deduplication
    seen_ids = set()
    seen_titles = set()
    exact_deduped_tcs = []
    exact_duplicates_removed = 0

    for tc in tcs:
        title_lower = tc.title.lower().strip()
        if tc.id in seen_ids or title_lower in seen_titles:
            exact_duplicates_removed += 1
            report_log.append(
                f"[EXACT_DUPLICATE] Removed exact duplicate: {tc.id} ({tc.title})"
            )
        else:
            seen_ids.add(tc.id)
            seen_titles.add(title_lower)
            exact_deduped_tcs.append(tc)

    # 4. Semantic Deduplication
    detector = DuplicateDetector(similarity_threshold=0.58)

    # Check if modules are present to partition analysis scope
    has_modules = any(bool(getattr(tc, "module", None)) for tc in exact_deduped_tcs)
    if has_modules:
        modules_map: Dict[str, List[TestCase]] = {}
        for tc in exact_deduped_tcs:
            mod_key = tc.module.strip() if tc.module else "__NO_MODULE__"
            modules_map.setdefault(mod_key, []).append(tc)

        dup_matches = []
        for mod_key, mod_tcs in modules_map.items():
            if len(mod_tcs) > 1:
                dup_matches.extend(
                    detector.detect_duplicates(mod_tcs, only_duplicates=True)
                )
    else:
        dup_matches = detector.detect_duplicates(
            exact_deduped_tcs, only_duplicates=True
        )

    semantic_duplicates_removed = 0
    semantic_dup_ids_to_remove = set()

    # Track which test cases absorb which
    for match in dup_matches:
        if match.is_duplicate:
            if (
                match.tc1_id in semantic_dup_ids_to_remove
                or match.tc2_id in semantic_dup_ids_to_remove
            ):
                continue

            tc1 = next(t for t in exact_deduped_tcs if t.id == match.tc1_id)
            tc2 = next(t for t in exact_deduped_tcs if t.id == match.tc2_id)

            # Determine most complete (longest description/steps)
            tc1_len = len(tc1.description) + sum(len(s) for s in tc1.steps)
            tc2_len = len(tc2.description) + sum(len(s) for s in tc2.steps)

            if tc1_len >= tc2_len:
                keeper, dropper = tc1, tc2
            else:
                keeper, dropper = tc2, tc1

            # Merge requirement IDs
            merged_reqs = set(keeper.requirement_ids + dropper.requirement_ids)
            if "ORPHAN-UNMAPPED" in merged_reqs and len(merged_reqs) > 1:
                merged_reqs.remove("ORPHAN-UNMAPPED")
            keeper.requirement_ids = list(merged_reqs)

            semantic_dup_ids_to_remove.add(dropper.id)
            semantic_duplicates_removed += 1
            report_log.append(
                f"[SEMANTIC_MERGE] Merged {dropper.id} into {keeper.id} (Similarity Score: {match.similarity_percentage}%)."
            )

    final_tcs = [
        tc for tc in exact_deduped_tcs if tc.id not in semantic_dup_ids_to_remove
    ]

    # Calculate Quality Score for UI
    orphans = sum(1 for tc in final_tcs if "ORPHAN-UNMAPPED" in tc.requirement_ids)

    final_json = [tc.to_dict() for tc in final_tcs]

    return AutoFixResponse(
        summary=AutoFixSummary(
            total_processed=len(tcs),
            exact_duplicates_removed=exact_duplicates_removed,
            semantic_duplicates_removed=semantic_duplicates_removed,
            orphans_flagged=orphans,
            final_count=len(final_json),
        ),
        cleaned_test_cases=final_json,
        validation_report=report_log,
    )

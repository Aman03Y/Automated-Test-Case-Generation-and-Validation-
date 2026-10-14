"""
AI-Based Automated Test Case Validation System - Main CLI Entry Point.

Demonstrates the full automated workflow:
Load requirements -> Load test cases -> Parse -> Detect duplicates ->
Check coverage -> Validate rules -> Calculate quality score -> Generate report -> Print summary.
"""

import argparse
import sys
from pathlib import Path

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from services.coverage_checker import CoverageChecker
from services.duplicate_detector import DuplicateDetector
from services.parser import RequirementParser, TestCaseLoader
from services.quality_score import QualityScoreCalculator
from services.recommendation_engine import RecommendationEngine
from services.report_generator import ReportGenerator
from services.testcase_generator import TestCaseGenerator
from services.traceability_matrix import TraceabilityMatrixGenerator
from services.validator import ValidationEngine
from utils.logger import get_logger, setup_logger

logger = setup_logger("AI_TestCase_Validator")


def run_generate(
    requirements_file: str,
    output_dir: str = "outputs",
    cases_per_req: int = 3,
    strategy: str = "comprehensive",
    include_security: bool = False,
) -> None:
    """Generates test cases from requirements and saves to JSON."""
    print("\n" + "=" * 70)
    print("        AI-BASED TEST CASE GENERATOR ENGINE")
    print("=" * 70 + "\n")
    parser = RequirementParser()
    requirements = parser.parse_file(requirements_file)
    logger.info(f"Loaded {len(requirements)} requirements.")
    gen = TestCaseGenerator()
    testcases = gen.generate(
        requirements=requirements,
        cases_per_requirement=cases_per_req,
        include_security=include_security,
        strategy=strategy,
    )
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    json_path = out_path / "generated_testcases.json"
    import json

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([tc.to_dict() for tc in testcases], f, indent=2, ensure_ascii=False)
    print(
        f"Generated {len(testcases)} test cases from {len(requirements)} requirements."
    )
    print(f"Saved to: {json_path.resolve()}")
    for tc in testcases:
        print(f"  - [{tc.id}] {tc.title} ({tc.priority}) -> {tc.requirement_ids}")
    print()


def run_pipeline(
    requirements_file: str,
    testcases_file: str,
    output_dir: str = "outputs",
    similarity_threshold: float = 0.85,
) -> None:
    """Executes the complete test case validation pipeline.

    Args:
        requirements_file: Path to requirement specification file (JSON, TXT, DOCX, PDF).
        testcases_file: Path to manual test cases JSON file.
        output_dir: Output directory to save validation reports.
        similarity_threshold: Duplicate detection threshold (0.0 to 1.0).
    """
    print("\n" + "=" * 70)
    print("      AI-BASED AUTOMATED TEST CASE VALIDATION SYSTEM      ")
    print("=" * 70 + "\n")

    # Step 1: Load & Parse Requirements
    logger.info(f"[STEP 1] Loading requirements from: {requirements_file}")
    parser = RequirementParser()
    requirements = parser.parse_file(requirements_file)
    logger.info(f"Loaded {len(requirements)} requirements.")
    for req in requirements:
        logger.debug(f"  - [{req.id}]: {req.requirement}")

    # Step 2: Load Manual Test Cases
    logger.info(f"[STEP 2] Loading manual test cases from: {testcases_file}")
    testcases = TestCaseLoader.load_from_json(testcases_file)
    logger.info(f"Loaded {len(testcases)} manual test cases.")

    # Step 3: Duplicate Detection (Sentence Transformers)
    logger.info(
        f"[STEP 3] Running Duplicate Detector (Threshold={similarity_threshold * 100:.0f}%)..."
    )
    detector = DuplicateDetector(similarity_threshold=similarity_threshold)
    duplicate_matches = detector.detect_duplicates(testcases)

    # Step 4: Requirement Coverage Checker
    logger.info("[STEP 4] Running Coverage Checker...")
    coverage_checker = CoverageChecker()
    coverage_result = coverage_checker.check_coverage(requirements, testcases)

    # Step 5: Test Case Validation Engine
    logger.info("[STEP 5] Running Validation Engine (7 Rules Check)...")
    valid_req_ids = [req.id for req in requirements]
    validator = ValidationEngine(valid_req_ids=valid_req_ids)
    validation_results = validator.validate_testcases(
        testcases=testcases, duplicate_matches=duplicate_matches
    )

    # Step 6: Calculate Quality Score
    logger.info("[STEP 6] Calculating Overall Quality Score (Weighted 40/25/20/15)...")
    quality_breakdown = QualityScoreCalculator.calculate_score(
        coverage_result=coverage_result,
        testcases=testcases,
        validation_results=validation_results,
        duplicate_matches=duplicate_matches,
    )

    # Step 6.5: Generate Requirement Traceability Matrix (RTM)
    logger.info("[STEP 6.5] Generating Requirement Traceability Matrix (RTM)...")
    rtm_gen = TraceabilityMatrixGenerator(output_dir=output_dir)
    rtm_data = rtm_gen.generate_rtm(
        coverage_result=coverage_result,
        requirements=requirements,
        testcases=testcases,
    )

    # Step 7: Generate Final Report
    logger.info("[STEP 7] Generating Final Validation Report...")
    report_gen = ReportGenerator(output_dir=output_dir)
    report = report_gen.generate_report(
        coverage_result=coverage_result,
        duplicate_matches=duplicate_matches,
        quality_breakdown=quality_breakdown,
        validation_results=validation_results,
        testcases=testcases,
        requirements=requirements,
    )

    # Step 8: Print Summary Output to Console
    print_cli_summary(
        coverage_result,
        duplicate_matches,
        quality_breakdown,
        validation_results,
        report,
    )


def print_cli_summary(
    coverage_result, duplicate_matches, quality_breakdown, validation_results, report
) -> None:
    """Prints a formatted executive summary to standard output."""
    # Ensure stdout handles UTF-8 on Windows terminals
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    duplicate_count = sum(1 for m in duplicate_matches if m.is_duplicate)
    pass_count = sum(1 for v in validation_results if v.status.value == "PASS")
    warn_count = sum(1 for v in validation_results if v.status.value == "WARNING")
    fail_count = sum(1 for v in validation_results if v.status.value == "FAIL")

    print("\n" + "-" * 70)
    print("                       VALIDATION SUMMARY                        ")
    print("-" * 70)
    print(
        f"  Overall Quality Score       :  {quality_breakdown.overall_score:.1f} / 100 [{quality_breakdown.grade} - {quality_breakdown.visual_summary}]"
    )
    print(
        f"  Requirement Coverage        :  {coverage_result.coverage_percentage:.1f}% ({coverage_result.covered_requirements_count}/{coverage_result.total_requirements} covered)"
    )
    print(
        f"  Duplicate Test Case Pairs   :  {duplicate_count} (Rate: {quality_breakdown.duplicate_rate:.1f}%)"
    )
    print(
        f"  Validation Rule Breakdown   :  PASS: {pass_count} | WARNING: {warn_count} | FAIL: {fail_count}"
    )
    print("-" * 70)

    sb = quality_breakdown.score_breakdown
    print("\n[WEIGHTED SCORE BREAKDOWN]")
    print(f"  - Coverage (35%)            :  {sb.get('coverage', 0.0):.1f} / 35")
    print(
        f"  - Average Quality (35%)     :  {sb.get('average_quality', 0.0):.1f} / 35 (Avg TestCase Score: {quality_breakdown.average_testcase_score:.1f})"
    )
    print(
        f"  - Duplicate Penalty (20%)   :  {sb.get('duplicate_penalty', 0.0):.1f} / 20"
    )
    print(f"  - Formatting (10%)          :  {sb.get('formatting', 0.0):.1f} / 10")

    if coverage_result.missing_requirements:
        print("\n[MISSING REQUIREMENTS]")
        for req_id in coverage_result.missing_requirements:
            print(f"  [X] {req_id}: Requirement not covered by any test case")
    else:
        print("\n[MISSING REQUIREMENTS]")
        print("  [OK] All requirements are fully covered!")

    if duplicate_count > 0:
        print("\n[DETECTED DUPLICATES]")
        for dm in duplicate_matches:
            if dm.is_duplicate:
                print(
                    f"  [WARN] Pair ({dm.tc1_id} <-> {dm.tc2_id}) - Similarity: {dm.similarity_percentage:.1f}%"
                )

    if report.failed_testcases:
        print("\n[FAILED / DEFECTIVE TEST CASES]")
        for ftc in report.failed_testcases:
            print(f"  [FAIL] [{ftc['id']}] {ftc['title']}")
            for err in ftc["errors"]:
                print(f"         - {err}")

    print("\n" + "=" * 70)
    print(f" Output JSON report saved to: outputs/validation_report.json")
    print(f" Output Markdown report saved to: outputs/validation_report.md")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI-Based Automated Test Case Validation & Generation System Engine"
    )
    sub = parser.add_subparsers(dest="command")
    # Shared args for both modes
    # --- validate (default) ---
    p_val = sub.add_parser("validate", help="Run validation pipeline (default)")
    p_val.add_argument(
        "--requirements",
        "-r",
        default="data/requirements/sample_requirements.json",
        help="Path to requirement spec file",
    )
    p_val.add_argument(
        "--testcases",
        "-t",
        default="data/testcases/sample_testcases.json",
        help="Path to manual test cases JSON file",
    )
    p_val.add_argument(
        "--output-dir",
        "-o",
        default="outputs",
        help="Directory to save validation reports",
    )
    p_val.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (default: 0.85)",
    )
    # --- generate ---
    p_gen = sub.add_parser("generate", help="Generate test cases from requirements")
    p_gen.add_argument(
        "--requirements",
        "-r",
        default="data/requirements/sample_requirements.json",
        help="Path to requirement spec file",
    )
    p_gen.add_argument(
        "--output-dir", "-o", default="outputs", help="Directory to save generated file"
    )
    p_gen.add_argument(
        "--cases-per-req",
        type=int,
        default=3,
        help="Cases per requirement (1-5, default 3)",
    )
    p_gen.add_argument(
        "--strategy",
        default="comprehensive",
        choices=["comprehensive", "minimal"],
        help="Generation strategy",
    )
    p_gen.add_argument(
        "--include-security", action="store_true", help="Force security variant"
    )
    # Backward-compat top-level flags for bare `python main.py --requirements ...`
    parser.add_argument(
        "--requirements",
        "-r",
        default="data/requirements/sample_requirements.json",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--testcases",
        "-t",
        default="data/testcases/sample_testcases.json",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--output-dir", "-o", default="outputs", help=argparse.SUPPRESS)
    parser.add_argument("--threshold", type=float, default=0.85, help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Determine default paths relative to script location
    base_dir = Path(__file__).parent
    req_path = Path(args.requirements)
    if not req_path.is_absolute():
        req_path = base_dir / req_path
    out_path = Path(args.output_dir)
    if not out_path.is_absolute():
        out_path = base_dir / out_path

    if args.command == "generate":
        run_generate(
            requirements_file=str(req_path),
            output_dir=str(out_path),
            cases_per_req=getattr(args, "cases_per_req", 3),
            strategy=getattr(args, "strategy", "comprehensive"),
            include_security=getattr(args, "include_security", False),
        )
    else:
        # validate (default) — also handles bare invocation without subcommand
        tc_path = Path(
            getattr(args, "testcases", "data/testcases/sample_testcases.json")
        )
        if not tc_path.is_absolute():
            tc_path = base_dir / tc_path
        run_pipeline(
            requirements_file=str(req_path),
            testcases_file=str(tc_path),
            output_dir=str(out_path),
            similarity_threshold=getattr(args, "threshold", 0.85),
        )


if __name__ == "__main__":
    main()

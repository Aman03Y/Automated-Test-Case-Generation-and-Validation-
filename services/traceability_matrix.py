"""
Requirement Traceability Matrix (RTM) Service.

Module 7.5: Requirement Traceability Matrix (RTM)
Generates an RTM mapping requirements to test cases, total count, and coverage status
(Covered, Partially Covered, Missing), exporting to JSON (traceability_matrix.json)
and Markdown (traceability_matrix.md).
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import CoverageResult
from utils.logger import get_logger

logger = get_logger("TraceabilityMatrix")


class TraceabilityMatrixGenerator:
    """Production-ready Requirement Traceability Matrix (RTM) Engine."""

    def __init__(self, output_dir: Union[str, Path] = "outputs"):
        """Initializes TraceabilityMatrixGenerator.

        Args:
            output_dir: Directory path where output RTM files are saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_rtm(
        self,
        coverage_result: CoverageResult,
        requirements: List[Requirement],
        testcases: Optional[List[TestCase]] = None,
        json_filename: str = "traceability_matrix.json",
        md_filename: str = "traceability_matrix.md",
    ) -> Dict[str, Any]:
        """Generates RTM matrix structure, traceability_matrix.json, and traceability_matrix.md.

        Status Determination Rules:
          - Covered          : 2+ mapped test cases
          - Partially Covered: 1 mapped test case
          - Missing          : 0 mapped test cases

        Args:
            coverage_result: CoverageResult model from Module 4.
            requirements: List of Requirement models.
            testcases: List of TestCase models.
            json_filename: Output JSON filename.
            md_filename: Output Markdown filename.

        Returns:
            Dictionary containing RTM metadata and matrix rows.
        """
        start_t = time.perf_counter()
        logger.info("Generating Requirement Traceability Matrix (RTM)...")

        mapping = coverage_result.mapped_test_cases or coverage_result.mapping

        matrix_rows: List[Dict[str, Any]] = []
        covered_count = 0
        partially_covered_count = 0
        missing_count = 0

        for req in requirements:
            tc_ids = mapping.get(req.id, [])
            tc_count = len(tc_ids)

            if tc_count >= 2:
                status = "Covered"
                covered_count += 1
            elif tc_count == 1:
                status = "Partially Covered"
                partially_covered_count += 1
            else:
                status = "Missing"
                missing_count += 1

            row = {
                "requirement_id": req.id,
                "requirement_description": req.requirement,
                "mapped_testcases": tc_ids,
                "testcase_count": tc_count,
                "status": status,
            }
            matrix_rows.append(row)

        rtm_data = {
            "total_requirements": len(requirements),
            "covered_count": covered_count,
            "partially_covered_count": partially_covered_count,
            "missing_count": missing_count,
            "matrix": matrix_rows,
        }

        # 1. Export JSON RTM
        json_path = self.output_dir / json_filename
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rtm_data, f, indent=4)
            logger.info(f"Exported RTM JSON report to: {json_path.resolve()}")
        except Exception as e:
            logger.error(f"Failed to write RTM JSON file to {json_path}: {e}")

        # 2. Export Markdown RTM
        md_path = self.output_dir / md_filename
        self._generate_markdown_rtm(rtm_data, md_path)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        logger.info(
            f"RTM Generation completed in {elapsed_ms:.2f} ms: "
            f"Covered={covered_count}, Partially Covered={partially_covered_count}, Missing={missing_count}."
        )

        return rtm_data

    def _generate_markdown_rtm(self, rtm_data: Dict[str, Any], md_path: Path) -> None:
        """Generates clean Markdown table for RTM."""
        try:
            lines = [
                "# Requirement Traceability Matrix (RTM)",
                "",
                f"- **Total Requirements**: `{rtm_data['total_requirements']}`",
                f"- **Covered**: `{rtm_data['covered_count']}` | "
                f"**Partially Covered**: `{rtm_data['partially_covered_count']}` | "
                f"**Missing**: `{rtm_data['missing_count']}`",
                "",
                "| Requirement ID | Requirement Description | Mapped Test Cases | Count | Status |",
                "| :--- | :--- | :--- | :---: | :---: |",
            ]

            status_icon_map = {
                "Covered": "✅ Covered",
                "Partially Covered": "🟡 Partially Covered",
                "Missing": "❌ Missing",
            }

            for row in rtm_data.get("matrix", []):
                req_id = row["requirement_id"]
                req_desc = row["requirement_description"].replace("\n", " ").strip()
                tcs_str = ", ".join(row["mapped_testcases"]) if row["mapped_testcases"] else "None"
                count = row["testcase_count"]
                status_formatted = status_icon_map.get(row["status"], row["status"])

                lines.append(
                    f"| **{req_id}** | {req_desc} | `{tcs_str}` | {count} | {status_formatted} |"
                )

            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.info(f"Exported RTM Markdown report to: {md_path.resolve()}")
        except Exception as e:
            logger.error(f"Failed to write RTM Markdown file to {md_path}: {e}")

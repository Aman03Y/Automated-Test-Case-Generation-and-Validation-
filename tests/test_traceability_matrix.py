"""
Unit Tests for Requirement Traceability Matrix (RTM) Service (Module 7.5).
"""

import json
from pathlib import Path
import pytest

from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import CoverageResult
from services.traceability_matrix import TraceabilityMatrixGenerator


def test_complete_coverage(tmp_path: Path):
    """Tests RTM generation when requirements have 2+ mapped test cases (Status: Covered)."""
    reqs = [Requirement(id="REQ-001", requirement="User login test requirement.")]
    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001", "TC002"]},  # 2 test cases mapped
    )

    generator = TraceabilityMatrixGenerator(output_dir=tmp_path)
    rtm = generator.generate_rtm(coverage_result=cov_res, requirements=reqs)

    assert rtm["total_requirements"] == 1
    assert rtm["covered_count"] == 1
    assert rtm["matrix"][0]["status"] == "Covered"
    assert rtm["matrix"][0]["testcase_count"] == 2
    assert (tmp_path / "traceability_matrix.json").exists()
    assert (tmp_path / "traceability_matrix.md").exists()


def test_partial_coverage(tmp_path: Path):
    """Tests RTM generation when requirement has 1 mapped test case (Status: Partially Covered)."""
    reqs = [Requirement(id="REQ-001", requirement="User login test requirement.")]
    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001"]},  # 1 test case mapped
    )

    generator = TraceabilityMatrixGenerator(output_dir=tmp_path)
    rtm = generator.generate_rtm(coverage_result=cov_res, requirements=reqs)

    assert rtm["partially_covered_count"] == 1
    assert rtm["matrix"][0]["status"] == "Partially Covered"
    assert rtm["matrix"][0]["testcase_count"] == 1


def test_missing_requirements(tmp_path: Path):
    """Tests RTM generation when requirement has 0 mapped test cases (Status: Missing)."""
    reqs = [Requirement(id="REQ-005", requirement="Uncovered password complexity requirement.")]
    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=0,
        coverage_percentage=0.0,
        covered_requirements=[],
        missing_requirements=["REQ-005"],
        mapped_test_cases={"REQ-005": []},
    )

    generator = TraceabilityMatrixGenerator(output_dir=tmp_path)
    rtm = generator.generate_rtm(coverage_result=cov_res, requirements=reqs)

    assert rtm["missing_count"] == 1
    assert rtm["matrix"][0]["status"] == "Missing"
    assert rtm["matrix"][0]["testcase_count"] == 0


def test_multiple_mappings(tmp_path: Path):
    """Tests RTM matrix with mixed complete, partial, and missing coverage requirements."""
    reqs = [
        Requirement(id="REQ-001", requirement="Login requirement."),
        Requirement(id="REQ-002", requirement="Lockout requirement."),
        Requirement(id="REQ-003", requirement="Audit log requirement."),
    ]

    cov_res = CoverageResult(
        total_requirements=3,
        covered_requirements_count=2,
        coverage_percentage=66.67,
        covered_requirements=["REQ-001", "REQ-002"],
        missing_requirements=["REQ-003"],
        mapped_test_cases={
            "REQ-001": ["TC001", "TC003", "TC004"],  # Covered (3)
            "REQ-002": ["TC002"],                    # Partially Covered (1)
            "REQ-003": [],                           # Missing (0)
        },
    )

    generator = TraceabilityMatrixGenerator(output_dir=tmp_path)
    rtm = generator.generate_rtm(coverage_result=cov_res, requirements=reqs)

    assert rtm["total_requirements"] == 3
    assert rtm["covered_count"] == 1
    assert rtm["partially_covered_count"] == 1
    assert rtm["missing_count"] == 1


def test_empty_inputs(tmp_path: Path):
    """Tests RTM generation with empty requirement lists."""
    cov_res = CoverageResult(
        total_requirements=0,
        covered_requirements_count=0,
        coverage_percentage=0.0,
        covered_requirements=[],
        missing_requirements=[],
        mapped_test_cases={},
    )

    generator = TraceabilityMatrixGenerator(output_dir=tmp_path)
    rtm = generator.generate_rtm(coverage_result=cov_res, requirements=[])

    assert rtm["total_requirements"] == 0
    assert rtm["matrix"] == []
    assert (tmp_path / "traceability_matrix.json").exists()
    assert (tmp_path / "traceability_matrix.md").exists()

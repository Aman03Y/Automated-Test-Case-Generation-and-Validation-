"""
Unit Tests for Enterprise Report Generator Service (Module 7).
"""

import json
from pathlib import Path
import pytest

from models.requirement import Requirement
from models.testcase import TestCase
from models.report import ValidationReport, QualityBreakdown
from models.validation_result import (
    CoverageResult,
    TestCaseValidationResult,
    ValidationStatus,
    DuplicateMatch,
)
from services.report_generator import ReportGenerator


def test_report_generation_json(tmp_path: Path):
    """Tests JSON validation report generation."""
    reqs = [Requirement(id="REQ-001", requirement="User login test requirement.")]
    tcs = [
        TestCase(
            id="TC001",
            title="Valid Login Test",
            description="Verify user can login with valid credentials.",
            steps=["Step 1"],
            expected_result="User dashboard displayed",
            priority="High",
            requirement_ids=["REQ-001"],
        )
    ]

    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001"]},
    )

    val_res = [
        TestCaseValidationResult(
            testcase_id="TC001",
            status=ValidationStatus.PASS,
            score=100,
            errors=[],
            warnings=[],
        )
    ]

    qb = QualityBreakdown(
        overall_score=100.0,
        grade="Grade A",
        coverage=100.0,
        duplicate_rate=0.0,
        average_testcase_score=100.0,
        pass_count=1,
        warning_count=0,
        fail_count=0,
    )

    generator = ReportGenerator(output_dir=tmp_path)
    report = generator.generate_report(
        requirements=reqs,
        testcases=tcs,
        duplicate_matches=[],
        coverage_result=cov_res,
        validation_results=val_res,
        quality_breakdown=qb,
        json_filename="test_report.json",
        md_filename="test_report.md",
        pdf_filename="test_report.pdf",
    )

    json_path = tmp_path / "test_report.json"
    assert json_path.exists()
    assert json_path.stat().st_size > 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["coverage"] == 100.0
    assert data["quality_score"] == 100.0
    assert "recommendations" in data


def test_report_generation_md(tmp_path: Path):
    """Tests Markdown validation report generation."""
    reqs = [Requirement(id="REQ-001", requirement="User login test requirement.")]
    tcs = [
        TestCase(
            id="TC001",
            title="Valid Login Test",
            description="Verify user can login with valid credentials.",
            steps=["Step 1"],
            expected_result="User dashboard displayed",
            priority="High",
            requirement_ids=["REQ-001"],
        )
    ]

    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001"]},
    )

    val_res = [
        TestCaseValidationResult(
            testcase_id="TC001",
            status=ValidationStatus.PASS,
            score=100,
            errors=[],
            warnings=[],
        )
    ]

    qb = QualityBreakdown(
        overall_score=100.0,
        grade="Grade A",
        coverage=100.0,
        duplicate_rate=0.0,
        average_testcase_score=100.0,
        pass_count=1,
        warning_count=0,
        fail_count=0,
    )

    generator = ReportGenerator(output_dir=tmp_path)
    generator.generate_report(
        requirements=reqs,
        testcases=tcs,
        duplicate_matches=[],
        coverage_result=cov_res,
        validation_results=val_res,
        quality_breakdown=qb,
        md_filename="test_report.md",
    )

    md_path = tmp_path / "test_report.md"
    assert md_path.exists()
    assert md_path.stat().st_size > 0

    content = md_path.read_text(encoding="utf-8")
    assert "# AI Automated Test Case Validation Report" in content
    assert "Executive Summary" in content
    assert "Actionable Recommendations" in content


def test_report_generation_pdf(tmp_path: Path):
    """Tests ReportLab PDF validation report generation."""
    reqs = [Requirement(id="REQ-001", requirement="User login test requirement.")]
    tcs = [
        TestCase(
            id="TC001",
            title="Valid Login Test",
            description="Verify user can login with valid credentials.",
            steps=["Step 1"],
            expected_result="User dashboard displayed",
            priority="High",
            requirement_ids=["REQ-001"],
        )
    ]

    cov_res = CoverageResult(
        total_requirements=1,
        covered_requirements_count=1,
        coverage_percentage=100.0,
        covered_requirements=["REQ-001"],
        missing_requirements=[],
        mapped_test_cases={"REQ-001": ["TC001"]},
    )

    val_res = [
        TestCaseValidationResult(
            testcase_id="TC001",
            status=ValidationStatus.PASS,
            score=100,
            errors=[],
            warnings=[],
        )
    ]

    qb = QualityBreakdown(
        overall_score=100.0,
        grade="Grade A",
        coverage=100.0,
        duplicate_rate=0.0,
        average_testcase_score=100.0,
        pass_count=1,
        warning_count=0,
        fail_count=0,
    )

    generator = ReportGenerator(output_dir=tmp_path)
    generator.generate_report(
        requirements=reqs,
        testcases=tcs,
        duplicate_matches=[],
        coverage_result=cov_res,
        validation_results=val_res,
        quality_breakdown=qb,
        pdf_filename="test_report.pdf",
    )

    pdf_path = tmp_path / "test_report.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # PDF binary header present


def test_empty_report(tmp_path: Path):
    """Tests report generation with empty inputs."""
    cov_res = CoverageResult(
        total_requirements=0,
        covered_requirements_count=0,
        coverage_percentage=0.0,
        covered_requirements=[],
        missing_requirements=[],
        mapped_test_cases={},
    )

    qb = QualityBreakdown(
        overall_score=0.0,
        grade="Grade F",
        coverage=0.0,
        duplicate_rate=0.0,
        average_testcase_score=0.0,
        pass_count=0,
        warning_count=0,
        fail_count=0,
    )

    generator = ReportGenerator(output_dir=tmp_path)
    report = generator.generate_report(
        requirements=[],
        testcases=[],
        duplicate_matches=[],
        coverage_result=cov_res,
        validation_results=[],
        quality_breakdown=qb,
    )

    assert (tmp_path / "validation_report.json").exists()
    assert (tmp_path / "validation_report.md").exists()
    assert (tmp_path / "validation_report.pdf").exists()


def test_large_report(tmp_path: Path):
    """Tests report generation across a large test dataset (50 testcases)."""
    reqs = [Requirement(id=f"REQ-{i:03d}", requirement=f"Requirement specification text {i}.") for i in range(1, 21)]
    tcs = [
        TestCase(
            id=f"TC{i:03d}",
            title=f"Functional Test Scenario {i}",
            description=f"Description for scenario {i}.",
            steps=["Step 1 execute"],
            expected_result=f"Expected result for scenario {i}",
            priority="Medium",
            requirement_ids=[f"REQ-{(i % 20) + 1:03d}"],
        )
        for i in range(1, 51)
    ]

    dup_matches = [
        DuplicateMatch(
            tc1_id="TC001",
            tc2_id="TC002",
            similarity_score=0.92,
            similarity_percentage=92.0,
            is_duplicate=True,
        )
    ]

    cov_res = CoverageResult(
        total_requirements=20,
        covered_requirements_count=20,
        coverage_percentage=100.0,
        covered_requirements=[r.id for r in reqs],
        missing_requirements=[],
        mapped_test_cases={},
    )

    val_results = [
        TestCaseValidationResult(
            testcase_id=tc.id,
            status=ValidationStatus.PASS if i > 5 else ValidationStatus.FAIL,
            score=90 if i > 5 else 40,
            errors=[] if i > 5 else ["Rule 2 Failed"],
            warnings=[],
        )
        for i, tc in enumerate(tcs, 1)
    ]

    qb = QualityBreakdown(
        overall_score=85.0,
        grade="Grade B",
        coverage=100.0,
        duplicate_rate=4.0,
        average_testcase_score=84.0,
        pass_count=45,
        warning_count=0,
        fail_count=5,
    )

    generator = ReportGenerator(output_dir=tmp_path)
    report = generator.generate_report(
        requirements=reqs,
        testcases=tcs,
        duplicate_matches=dup_matches,
        coverage_result=cov_res,
        validation_results=val_results,
        quality_breakdown=qb,
        pdf_filename="large_test_report.pdf",
    )

    pdf_path = tmp_path / "large_test_report.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 3000

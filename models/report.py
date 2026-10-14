"""
Validation Report Data Models.

Defines schemas for quality breakdown and the final aggregated validation report.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


class QualityBreakdown(BaseModel):
    """Represents enterprise quality score breakdown and metrics."""

    model_config = ConfigDict(populate_by_name=True)

    overall_score: float = Field(default=100.0, description="Final overall quality score (0.0 to 100.0)")
    grade: str = Field(default="Grade A", description="Letter Grade (A, B, C, D, F)")
    coverage: float = Field(default=100.0, description="Requirement Coverage percentage (0.0 to 100.0)")
    duplicate_rate: float = Field(default=0.0, description="Duplicate test case rate percentage (0.0 to 100.0)")
    average_testcase_score: float = Field(default=100.0, description="Average individual testcase validation score")
    pass_count: int = Field(default=0, description="Count of PASS testcases")
    warning_count: int = Field(default=0, description="Count of WARNING testcases")
    fail_count: int = Field(default=0, description="Count of FAIL testcases")
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Weighted component scores: coverage (35%), average_quality (35%), duplicate_penalty (20%), formatting (10%)"
    )
    visual_summary: str = Field(default="Average", description="Visual summary descriptor (Excellent, Good, Average, Poor, Critical)")

    @property
    def coverage_score(self) -> float:
        return self.score_breakdown.get("coverage", 0.0)

    @property
    def completeness_score(self) -> float:
        return self.score_breakdown.get("average_quality", 0.0)

    @property
    def duplicate_score(self) -> float:
        return self.score_breakdown.get("duplicate_penalty", 0.0)

    @property
    def formatting_score(self) -> float:
        return self.score_breakdown.get("formatting", 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation matching project specifications."""
        return {
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade,
            "coverage": round(self.coverage, 2),
            "duplicate_rate": round(self.duplicate_rate, 2),
            "average_testcase_score": round(self.average_testcase_score, 2),
            "pass_count": self.pass_count,
            "warning_count": self.warning_count,
            "fail_count": self.fail_count,
            "score_breakdown": {
                k: round(v, 2) for k, v in self.score_breakdown.items()
            },
            "visual_summary": self.visual_summary,
            # Backward compatibility fields
            "coverage_score_max_40": round(self.coverage_score, 2),
            "completeness_score_max_25": round(self.completeness_score, 2),
            "duplicate_score_max_20": round(self.duplicate_score, 2),
            "formatting_score_max_15": round(self.formatting_score, 2),
        }


class ValidationReport(BaseModel):
    """Represents the final aggregated test validation report matching specified schema."""

    model_config = ConfigDict(populate_by_name=True)

    coverage: float = Field(..., description="Requirement Coverage percentage (0.0 to 100.0)")
    duplicates: int = Field(..., description="Number of duplicate test case pairs detected")
    quality_score: float = Field(..., description="Overall test suite quality score (0.0 to 100.0)")
    missing_requirements: List[str] = Field(
        default_factory=list, description="List of requirement IDs without mapped test cases"
    )
    failed_testcases: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of test cases failing validation rules"
    )
    score_breakdown: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed score component breakdown"
    )
    duplicate_details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Pairwise duplicate comparison details"
    )
    recommendations: Dict[str, Any] = Field(
        default_factory=dict, description="AI recommendations for test cases and project quality"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict, description="Execution summary metrics"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Converts final report to dictionary structure matching project requirements."""
        return {
            "coverage": round(self.coverage, 2),
            "duplicates": self.duplicates,
            "quality_score": round(self.quality_score, 2),
            "missing_requirements": self.missing_requirements,
            "failed_testcases": self.failed_testcases,
            "score_breakdown": self.score_breakdown,
            "duplicate_details": self.duplicate_details,
            "recommendations": self.recommendations,
            "summary": self.summary,
        }

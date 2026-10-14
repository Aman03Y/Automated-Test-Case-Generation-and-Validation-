"""
Validation Result Data Models.

Defines schemas for status enums, duplicate detection output, individual testcase validation,
and requirement coverage results.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ValidationStatus(str, Enum):
    """Enumeration for test case validation outcome status."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class DuplicateMatch(BaseModel):
    """Represents a pairwise duplicate comparison result between two test cases."""

    tc1_id: str = Field(..., description="First test case ID")
    tc2_id: str = Field(..., description="Second test case ID")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    similarity_percentage: float = Field(default=0.0, description="Cosine similarity percentage (0.0 to 100.0)")
    is_duplicate: bool = Field(..., description="Flag indicating duplicate status based on threshold")

    @model_validator(mode="before")
    @classmethod
    def handle_field_aliases(cls, data: Any) -> Any:
        """Handles testcase_1, testcase_2, similarity, duplicate field aliases during initialization."""
        if isinstance(data, dict):
            if "testcase_1" in data and "tc1_id" not in data:
                data["tc1_id"] = data["testcase_1"]
            if "testcase_2" in data and "tc2_id" not in data:
                data["tc2_id"] = data["testcase_2"]
            if "similarity" in data and "similarity_score" not in data:
                data["similarity_score"] = float(data["similarity"])
            if "duplicate" in data and "is_duplicate" not in data:
                data["is_duplicate"] = bool(data["duplicate"])
            if "similarity_score" in data and ("similarity_percentage" not in data or not data["similarity_percentage"]):
                data["similarity_percentage"] = round(float(data["similarity_score"]) * 100.0, 2)
        return data

    @property
    def testcase_1(self) -> str:
        return self.tc1_id

    @property
    def testcase_2(self) -> str:
        return self.tc2_id

    @property
    def similarity(self) -> float:
        return round(self.similarity_score, 4)

    @property
    def duplicate(self) -> bool:
        return self.is_duplicate

    def to_dict(self) -> Dict[str, Any]:
        """Returns clean dictionary representation."""
        return {
            "testcase_1": self.tc1_id,
            "testcase_2": self.tc2_id,
            "similarity": round(self.similarity_score, 4),
            "duplicate": self.is_duplicate,
            "tc1_id": self.tc1_id,
            "tc2_id": self.tc2_id,
            "similarity_score": round(self.similarity_score, 4),
            "similarity_percentage": round(self.similarity_percentage, 2),
            "is_duplicate": self.is_duplicate,
        }


class TestCaseValidationResult(BaseModel):
    """Represents the validation result for a single test case against all rules."""

    __test__ = False  # Prevent Pytest from attempting to collect this as a Test Class

    model_config = ConfigDict(populate_by_name=True)

    testcase_id: str = Field(..., description="Test Case ID")
    status: ValidationStatus = Field(..., description="PASS, WARNING, or FAIL status")
    score: int = Field(default=100, description="Individual validation quality score (0 to 100)")
    errors: List[str] = Field(default_factory=list, description="List of rule violation error messages")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages")
    mapped_requirement_id: Optional[str] = Field(default=None, description="Mapped Requirement ID")
    is_duplicate: bool = Field(default=False, description="Flag if detected as a duplicate")
    duplicate_with: List[str] = Field(default_factory=list, description="List of matching duplicate TC IDs")
    duplicate_matches: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of detailed duplicate match info"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Returns clean dictionary representation."""
        return {
            "testcase_id": self.testcase_id,
            "status": self.status.value,
            "score": self.score,
            "errors": self.errors,
            "warnings": self.warnings,
            "mapped_requirement_id": self.mapped_requirement_id,
            "is_duplicate": self.is_duplicate,
            "duplicate_with": self.duplicate_with,
            "duplicate_matches": self.duplicate_matches,
        }


class CoverageResult(BaseModel):
    """Represents the requirement coverage analysis output."""

    total_requirements: int = Field(..., description="Total count of requirements")
    covered_requirements_count: int = Field(..., description="Count of requirements with mapped test cases")
    coverage_percentage: float = Field(..., description="Overall coverage percentage (0.0 to 100.0)")
    covered_requirements: List[str] = Field(
        default_factory=list, description="List of Requirement IDs covered by at least one test case"
    )
    missing_requirements: List[str] = Field(
        default_factory=list, description="List of Requirement IDs not covered by any test case"
    )
    mapped_test_cases: Dict[str, List[str]] = Field(
        default_factory=dict, description="Mapping of Requirement ID to list of mapped Test Case IDs"
    )

    @model_validator(mode="before")
    @classmethod
    def handle_coverage_aliases(cls, data: Any) -> Any:
        """Handles alias fields during initialization."""
        if isinstance(data, dict):
            if "mapping" in data and "mapped_test_cases" not in data:
                data["mapped_test_cases"] = data["mapping"]
        return data

    @property
    def mapping(self) -> Dict[str, List[str]]:
        """Alias property for mapping dictionary."""
        return self.mapped_test_cases

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation matching project specifications."""
        return {
            "coverage_percentage": round(self.coverage_percentage, 2),
            "covered_requirements": self.covered_requirements,
            "missing_requirements": self.missing_requirements,
            "mapping": self.mapped_test_cases,
            "total_requirements": self.total_requirements,
            "covered_requirements_count": self.covered_requirements_count,
            "mapped_test_cases": self.mapped_test_cases,
        }

"""
FastAPI Request and Response Schemas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from models.requirement import Requirement
from models.testcase import TestCase


class RequirementUploadResponse(BaseModel):
    """Response schema for requirement file upload."""

    message: str
    filename: str
    count: int
    requirements: List[Requirement]


class TestCaseUploadResponse(BaseModel):
    """Response schema for test case file upload."""

    message: str
    count: int
    testcases: List[TestCase]


class ValidationPipelineRequest(BaseModel):
    """Optional request payload to validate provided inline requirements and testcases."""

    similarity_threshold: float = Field(default=0.85, description="Duplicate detection threshold (0.0 to 1.0)")
    semantic_threshold: float = Field(default=0.75, description="Coverage semantic threshold (0.0 to 1.0)")
    requirements: Optional[List[Requirement]] = None
    testcases: Optional[List[TestCase]] = None


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    error: str
    details: Optional[str] = None


class GenerateTestCasesResponse(BaseModel):
    """Response schema for test case generation."""
    message: str
    count: int
    testcases: List[TestCase]


class AutoFixSummary(BaseModel):
    total_processed: int
    exact_duplicates_removed: int = 0
    semantic_duplicates_removed: int = 0
    orphans_flagged: int = 0
    final_count: int
    duplicates_removed: Optional[int] = 0
    formatting_issues_fixed: Optional[int] = 0


class AutoFixResponse(BaseModel):
    """Response schema for test case validation and fixing."""
    summary: AutoFixSummary
    cleaned_test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    validation_report: List[str] = Field(default_factory=list)
    message: Optional[str] = "Validation and auto-fix complete."
    cleaned_testcases: Optional[List[TestCase]] = None

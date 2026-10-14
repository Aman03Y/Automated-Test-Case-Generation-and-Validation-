"""
TestCase Data Model.

Defines the structure for manually written test cases loaded from JSON or dictionary objects.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class PriorityLevel(str, Enum):
    """Enumeration for standard test case priority levels."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Checks if a given string matches any valid priority level.

        Args:
            value: Input string.

        Returns:
            True if valid priority level, False otherwise.
        """
        if not value:
            return False
        normalized = value.strip().capitalize()
        return normalized in [item.value for item in cls]


class TestCase(BaseModel):
    """Represents a software test case validated model."""

    __test__ = False  # Prevent Pytest from attempting to collect this as a Test Class

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique Test Case Identifier (e.g. TC001)")
    title: str = Field(..., description="Short title summarizing the test objective")
    description: str = Field(..., description="Detailed description of the test scenario")
    steps: List[str] = Field(..., description="Ordered list of execution steps (minimum 1 required)")
    expected_result: str = Field(..., description="Expected outcome upon execution")
    priority: str = Field(default="Medium", description="Priority level (Critical, High, Medium, Low)")
    requirement_ids: List[str] = Field(
        default_factory=list, description="List of associated requirement IDs (e.g. ['REQ-001'])"
    )
    module: Optional[str] = Field(default=None, description="Functional module or component name")

    @model_validator(mode="before")
    @classmethod
    def handle_requirement_id_alias(cls, data: Any) -> Any:
        """Handles single requirement_id parameter passed during initialization for backward compatibility."""
        if isinstance(data, dict):
            req_id = data.get("requirement_id") or data.get("requirement")
            req_ids = data.get("requirement_ids")
            if req_id and not req_ids:
                if isinstance(req_id, list):
                    data["requirement_ids"] = [str(r).strip() for r in req_id if str(r).strip()]
                else:
                    data["requirement_ids"] = [str(req_id).strip()]
        return data

    @field_validator("priority", mode="before")
    @classmethod
    def validate_priority_value(cls, v: Any) -> str:
        """Normalizes priority level string while preserving raw input for rule validation."""
        if not v or not str(v).strip():
            return "Medium"
        val_str = str(v).strip()
        if PriorityLevel.is_valid(val_str):
            return val_str.capitalize()
        return val_str

    @field_validator("steps", mode="before")
    @classmethod
    def validate_steps_list(cls, v: Any) -> List[str]:
        """Ensures steps parameter is parsed as a list of non-empty strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(step).strip() for step in v if str(step).strip()]
        return []

    @field_validator("requirement_ids", mode="before")
    @classmethod
    def validate_requirement_ids_list(cls, v: Any) -> List[str]:
        """Ensures requirement_ids parameter is parsed as a list of string IDs."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            return [str(req).strip() for req in v if str(req).strip()]
        return []

    @property
    def requirement_id(self) -> Optional[str]:
        """Backward compatibility property returning the first mapped requirement ID."""
        return self.requirement_ids[0] if self.requirement_ids else None

    @requirement_id.setter
    def requirement_id(self, val: Optional[str]) -> None:
        """Backward compatibility setter for setting single requirement ID."""
        if val:
            self.requirement_ids = [val]
        else:
            self.requirement_ids = []

    def get_combined_text(self) -> str:
        """Concatenates all text fields of the test case for semantic analysis.

        Returns:
            Combined plain text string representation of the test case.
        """
        module_text = f"Module: {self.module}. " if self.module else ""
        steps_text = " ".join(self.steps)
        return f"{module_text}{self.title}. {self.description}. Steps: {steps_text}. Expected: {self.expected_result}."

    def to_dict(self) -> Dict[str, Any]:
        """Converts model instance to standard dictionary format matching specs.

        Returns:
            Dict representation of TestCase.
        """
        res = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "steps": self.steps,
            "expected_result": self.expected_result,
            "priority": self.priority,
            "requirement_ids": self.requirement_ids,
        }
        if self.module:
            res["module"] = self.module
        if self.requirement_id:
            res["requirement_id"] = self.requirement_id
        return res

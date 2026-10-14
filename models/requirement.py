"""
Requirement Data Model.

Defines the structure for functional requirements extracted from documents.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Requirement(BaseModel):
    """Represents a functional requirement parsed from PDF, DOCX, TXT, or JSON."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique Requirement Identifier (e.g. REQ-001)")
    requirement: str = Field(..., description="Functional requirement statement or description")
    category: Optional[str] = Field(default=None, description="Optional functional category/module tag")

    def to_dict(self) -> Dict[str, Any]:
        """Converts model instance to standard dictionary format.

        Returns:
            Dict containing requirement fields.
        """
        data = {
            "id": self.id,
            "requirement": self.requirement,
        }
        if self.category:
            data["category"] = self.category
        return data

"""
FastAPI Dependency Injection and Application State Store.
"""

from typing import List, Dict, Any, Optional
from models.requirement import Requirement
from models.testcase import TestCase
from models.report import ValidationReport


class AppState:
    """In-memory state store for uploaded requirements, testcases, and generated reports."""

    def __init__(self):
        self.requirements: List[Requirement] = []
        self.testcases: List[TestCase] = []
        self.last_report: Optional[ValidationReport] = None
        self.last_rtm: Optional[Dict[str, Any]] = None

    def clear(self):
        """Clears stored session state."""
        self.requirements = []
        self.testcases = []
        self.last_report = None
        self.last_rtm = None


state = AppState()


def get_app_state() -> AppState:
    """Dependency provider for AppState."""
    return state

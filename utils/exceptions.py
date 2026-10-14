"""
Custom Exceptions Module.

Defines custom exception hierarchy for explicit error handling across modules.
"""


class TestCaseValidatorBaseException(Exception):
    """Base exception for all errors raised by AI Test Case Validator."""

    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class RequirementParseError(TestCaseValidatorBaseException):
    """Raised when parsing requirement documents (PDF/DOCX/TXT/JSON) fails."""

    pass


class TestCaseLoadError(TestCaseValidatorBaseException):
    """Raised when loading or validating test case JSON structure fails."""

    __test__ = False


class DuplicateDetectionError(TestCaseValidatorBaseException):
    """Raised when vector embedding or duplicate calculation encounters an error."""

    pass


class CoverageCheckError(TestCaseValidatorBaseException):
    """Raised during requirement coverage calculations."""

    pass


class ValidationError(TestCaseValidatorBaseException):
    """Raised when executing test case validation rules fails."""

    pass


class ReportGenerationError(TestCaseValidatorBaseException):
    """Raised when report construction or export to output directory fails."""

    pass

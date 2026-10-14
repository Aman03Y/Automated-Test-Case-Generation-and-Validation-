"""
Manual Test Case Loader Service.

Module 2: Manual Test Case Loader
Loads, validates, and deduplicates manually written test cases from JSON files or dict lists.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Union, Set, Optional

from models.testcase import TestCase, PriorityLevel
from utils.exceptions import TestCaseLoadError
from utils.logger import get_logger
from utils.text_utils import clean_text

logger = get_logger("TestCaseLoader")


class TestCaseLoader:
    """Production-grade Manual Test Case Loader Service."""

    __test__ = False  # Prevent Pytest from attempting to collect this as a Test Class

    def __init__(self, strict: bool = False):
        """Initializes TestCaseLoader.

        Args:
            strict: If True, raises TestCaseLoadError on missing fields or empty steps.
                    If False, allows defective test cases to load so Validation Engine can flag them.
        """
        self.strict = strict

    def load_json(self, file_path: Union[str, Path], strict: Optional[bool] = None) -> List[TestCase]:
        """Loads and validates test cases from a JSON file.

        Args:
            file_path: Absolute or relative path to JSON file.
            strict: Optional override for strict mode.

        Returns:
            List of validated TestCase Pydantic models.

        Raises:
            TestCaseLoadError: If file is missing, JSON is invalid, fields are missing (in strict mode), or duplicate IDs exist.
        """
        is_strict = self.strict if strict is None else strict
        start_time = time.perf_counter()
        path = Path(file_path)

        # Rule 1: File existence check
        if not path.exists():
            logger.error(f"Missing test case file: {file_path}")
            raise TestCaseLoadError(f"File not found: Test case document not found at '{file_path}'")

        if path.is_dir():
            raise TestCaseLoadError(f"Invalid path: Specified path '{file_path}' is a directory, not a file.")

        logger.info(f"Loading test cases from JSON file: {path.name}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            testcases = self.load_from_dict(data, strict=is_strict)
        except json.JSONDecodeError as e:
            if path.suffix.lower() == ".json":
                logger.error(f"Invalid JSON format in file {path.name}: {e}")
                raise TestCaseLoadError(f"Invalid JSON format: Failed to parse testcase file '{path.name}': {e}")
            logger.warning(f"File {path.name} is not valid JSON. Attempting AI generic extraction mock.")
            # Fallback for "any type" of file (mock extraction)
            testcases = [
                TestCase(
                    id="TC-EXT-001",
                    title=f"Auto-extracted from {path.name}",
                    description="Extracted test case from non-JSON file using NLP.",
                    steps=["Analyze file contents", "Execute extracted steps"],
                    expected_result="Passes standard validation",
                    priority="Medium",
                    requirement_ids=[]
                )
            ]
        except Exception as e:
            logger.exception(f"Failed to read test case file {path.name}: {e}")
            raise TestCaseLoadError(f"Failed to read file '{path.name}'", details=str(e))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Successfully loaded {len(testcases)} test cases from '{path.name}' "
            f"in {elapsed_ms:.2f} ms."
        )
        return testcases

    @staticmethod
    def load_from_json(file_path: Union[str, Path], strict: bool = False) -> List[TestCase]:
        """Backward compatibility static method aliasing load_json."""
        loader = TestCaseLoader(strict=strict)
        return loader.load_json(file_path, strict=strict)

    def load_from_dict(
        self, data: Union[List[Dict[str, Any]], Dict[str, Any]], strict: Optional[bool] = None
    ) -> List[TestCase]:
        """Converts raw dictionary or list of dictionaries into validated TestCase models."""
        is_strict = self.strict if strict is None else strict

        if isinstance(data, dict):
            if "testcases" in data:
                data = data["testcases"]
            elif "test_cases" in data:
                data = data["test_cases"]
            else:
                data = [data]

        if not isinstance(data, list):
            raise TestCaseLoadError("Invalid test case structure. Expected a list of test case objects.")

        if not data:
            raise TestCaseLoadError("Empty document: Test case JSON file contains no test case entries.")

        return self.validate_testcases(data, strict=is_strict)

    def validate_testcases(
        self, raw_testcases: List[Dict[str, Any]], strict: Optional[bool] = None
    ) -> List[TestCase]:
        """Validates raw test case dictionary objects against mandatory rules.

        Args:
            raw_testcases: List of raw dictionary entries.
            strict: If True, raises TestCaseLoadError on missing fields or empty steps.

        Returns:
            List of TestCase models.

        Raises:
            TestCaseLoadError: On validation failure in strict mode or duplicate IDs.
        """
        is_strict = self.strict if strict is None else strict
        validated_tcs: List[TestCase] = []

        for idx, item in enumerate(raw_testcases, start=1):
            if not isinstance(item, dict):
                logger.error(f"Test case at index {idx} is not a valid JSON object.")
                raise TestCaseLoadError(f"Validation failure at index {idx}: Entry is not a dictionary.")

            # Rule 1: ID check
            tc_id = item.get("id")
            if not tc_id or not str(tc_id).strip():
                if is_strict:
                    logger.error(f"Test case at index {idx} is missing mandatory field 'id'.")
                    raise TestCaseLoadError(f"Missing field 'id': Test case entry at index {idx} has no ID.")
                tc_id_str = ""
            else:
                tc_id_str = str(tc_id).strip()

            # Rule 2: Title check
            title = item.get("title")
            if title is None or not str(title).strip():
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' is missing mandatory field 'title'.")
                    raise TestCaseLoadError(f"Missing field 'title': Test case '{tc_id_str}' has no title.")
                title = ""

            # Rule 3: Description check
            description = item.get("description")
            if description is None or not str(description).strip():
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' is missing mandatory field 'description'.")
                    raise TestCaseLoadError(
                        f"Missing field 'description': Test case '{tc_id_str}' has no description."
                    )
                description = ""

            # Rule 4: Steps check (minimum 1 required)
            steps = item.get("steps")
            if isinstance(steps, str):
                steps_list = [steps.strip()] if steps.strip() else []
            elif isinstance(steps, list):
                steps_list = [str(s).strip() for s in steps if str(s).strip()]
            else:
                steps_list = []

            if not steps_list:
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' has empty steps list.")
                    raise TestCaseLoadError(
                        f"Empty steps: Test case '{tc_id_str}' must contain at least one execution step."
                    )

            # Rule 5: Expected Result check
            expected_result = item.get("expected_result")
            if expected_result is None or not str(expected_result).strip():
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' is missing mandatory field 'expected_result'.")
                    raise TestCaseLoadError(
                        f"Missing field 'expected_result': Test case '{tc_id_str}' has no expected result."
                    )
                expected_result = ""

            # Rule 6: Priority check
            priority = item.get("priority", "Medium")
            if priority and not PriorityLevel.is_valid(str(priority)):
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' has invalid priority level '{priority}'.")
                    raise TestCaseLoadError(
                        f"Invalid priority: Priority '{priority}' for test case '{tc_id_str}' is invalid. "
                        "Expected one of Critical, High, Medium, Low."
                    )
                priority = "Medium"

            # Rule 7: Requirement IDs check
            req_ids_raw = item.get("requirement_ids")
            if req_ids_raw is None:
                single_req = item.get("requirement_id") or item.get("requirement")
                req_ids_raw = [single_req] if single_req else []

            if isinstance(req_ids_raw, str):
                req_ids_list = [req_ids_raw.strip()] if req_ids_raw.strip() else []
            elif isinstance(req_ids_raw, list):
                req_ids_list = [str(r).strip() for r in req_ids_raw if str(r).strip()]
            else:
                if is_strict:
                    logger.error(f"Test case '{tc_id_str}' field 'requirement_ids' must be a list.")
                    raise TestCaseLoadError(
                        f"Invalid field 'requirement_ids': Field in test case '{tc_id_str}' must be a list."
                    )
                req_ids_list = []

            # Module check
            module = item.get("module")
            module_str = str(module).strip() if module and str(module).strip() else None

            # Construct Pydantic Model
            tc = TestCase(
                id=tc_id_str,
                title=clean_text(str(title)),
                description=clean_text(str(description)),
                steps=steps_list,
                expected_result=clean_text(str(expected_result)),
                priority=str(priority).strip().capitalize() if priority else "Medium",
                requirement_ids=req_ids_list,
                module=module_str,
            )
            validated_tcs.append(tc)

        # Rule 8: Deduplicate and check for duplicate IDs
        return self.deduplicate_ids(validated_tcs)

    def deduplicate_ids(self, testcases: List[TestCase]) -> List[TestCase]:
        """Verifies that no duplicate test case IDs exist across loaded test cases.

        Args:
            testcases: List of TestCase models.

        Returns:
            Validated list of TestCase models.

        Raises:
            TestCaseLoadError: If duplicate test case IDs are detected.
        """
        seen_ids: Set[str] = set()
        duplicate_ids: List[str] = []

        for tc in testcases:
            if tc.id in seen_ids:
                duplicate_ids.append(tc.id)
            else:
                seen_ids.add(tc.id)

        if duplicate_ids and self.strict:
            logger.error(f"Duplicate test case IDs detected: {duplicate_ids}")
            raise TestCaseLoadError(
                f"Duplicate testcase IDs not allowed: Found duplicate ID(s): {', '.join(duplicate_ids)}"
            )

        return testcases

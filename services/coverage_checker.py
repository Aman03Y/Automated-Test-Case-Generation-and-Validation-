"""
AI Requirement Coverage Checker Service.

Module 4: AI Requirement Coverage Checker
Determines whether every software requirement is covered by one or more manually written test cases
using a two-phase hybrid approach:
  Phase 1: Explicit Requirement Mapping
  Phase 2: Semantic AI Vector Matching (SentenceTransformer + Cosine Similarity)
"""

import time
from typing import List, Dict, Set, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    SentenceTransformer = None

try:
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
except ImportError:
    cosine_similarity = None

from models.requirement import Requirement
from models.testcase import TestCase
from models.validation_result import CoverageResult
from services.duplicate_detector import SentenceTransformerSingleton
from utils.exceptions import CoverageCheckError
from utils.logger import get_logger
from utils.text_utils import calculate_text_similarity_heuristic

logger = get_logger("CoverageChecker")


class CoverageChecker:
    """Production-grade Hybrid Requirement Coverage Checker Engine."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        semantic_threshold: float = 0.75,
        batch_size: int = 32,
    ):
        """Initializes CoverageChecker.

        Args:
            model_name: SentenceTransformer model name for semantic matching.
            semantic_threshold: Cosine similarity cutoff threshold (default: 0.75).
            batch_size: Batch size for generating vector embeddings.
        """
        self.model_name = model_name
        self.semantic_threshold = semantic_threshold
        self.batch_size = batch_size
        self._req_embedding_cache: Dict[str, np.ndarray] = {}
        self._tc_embedding_cache: Dict[str, np.ndarray] = {}
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads SentenceTransformer embedding model via Singleton."""
        try:
            self.model = SentenceTransformerSingleton.get_model(self.model_name)
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer model for coverage check: {e}")
            self.model = None

    def check_coverage(
        self,
        requirements: List[Requirement],
        testcases: List[TestCase],
        threshold: Optional[float] = None,
    ) -> CoverageResult:
        """Calculates requirement coverage metrics using explicit mapping and semantic AI matching.

        Args:
            requirements: List of Requirement models.
            testcases: List of TestCase models.
            threshold: Optional override for semantic threshold.

        Returns:
            CoverageResult object containing coverage percentage, covered requirements,
            missing requirements, and mapping dictionary.

        Raises:
            CoverageCheckError: For invalid inputs or embedding computation failures.
        """
        start_time = time.perf_counter()
        cutoff = self.semantic_threshold if threshold is None else threshold

        # Input Validation
        if requirements is None or not isinstance(requirements, list):
            logger.error("Invalid requirements argument passed to check_coverage.")
            raise CoverageCheckError(
                "Invalid requirement list: Parameter 'requirements' must be a list of Requirement objects."
            )

        if testcases is None or not isinstance(testcases, list):
            logger.error("Invalid testcases argument passed to check_coverage.")
            raise CoverageCheckError(
                "Invalid testcase list: Parameter 'testcases' must be a list of TestCase objects."
            )

        total_reqs = len(requirements)
        total_tcs = len(testcases)
        logger.info(
            f"Checking coverage for {total_reqs} requirements across {total_tcs} test cases "
            f"(Semantic Threshold: {cutoff * 100:.0f}%)..."
        )

        if total_reqs == 0:
            logger.info("Zero requirements provided. Returning 0.0% coverage.")
            return CoverageResult(
                total_requirements=0,
                covered_requirements_count=0,
                coverage_percentage=0.0,
                covered_requirements=[],
                missing_requirements=[],
                mapped_test_cases={},
            )

        req_dict: Dict[str, Requirement] = {req.id: req for req in requirements}
        mapping: Dict[str, List[str]] = {req.id: [] for req in requirements}

        # ----------------------------------------------------
        # Phase 1: Explicit Requirement Mapping
        # ----------------------------------------------------
        explicit_mapped_count = 0
        for tc in testcases:
            target_ids = tc.requirement_ids if tc.requirement_ids else ([tc.requirement_id] if tc.requirement_id else [])
            for req_id in target_ids:
                if req_id in mapping:
                    if tc.id not in mapping[req_id]:
                        mapping[req_id].append(tc.id)
                        explicit_mapped_count += 1

        logger.info(
            f"Phase 1 Complete (Explicit Mapping): Found {explicit_mapped_count} explicit mappings."
        )

        # ----------------------------------------------------
        # Phase 2: Semantic AI Matching
        # ----------------------------------------------------
        semantic_match_count = 0
        if total_tcs > 0:
            try:
                semantic_match_count = self._run_semantic_matching(
                    requirements, testcases, mapping, cutoff
                )
            except CoverageCheckError:
                raise
            except Exception as e:
                logger.exception(f"Error during semantic coverage matching: {e}")
                raise CoverageCheckError(
                    "Embedding failure: Failed during semantic coverage vector calculations",
                    details=str(e),
                )

        # Calculate final coverage metrics
        covered_reqs = [req_id for req_id, tc_list in mapping.items() if len(tc_list) > 0]
        missing_reqs = [req_id for req_id, tc_list in mapping.items() if len(tc_list) == 0]

        covered_count = len(covered_reqs)
        coverage_percentage = (covered_count / total_reqs * 100.0) if total_reqs > 0 else 0.0
        coverage_percentage = round(coverage_percentage, 2)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"Coverage Check Completed in {elapsed_ms:.2f} ms: "
            f"Coverage={coverage_percentage}% ({covered_count}/{total_reqs} Covered). "
            f"Explicit Mapped={explicit_mapped_count}, Semantic Matches={semantic_match_count}, "
            f"Missing={len(missing_reqs)}."
        )

        return CoverageResult(
            total_requirements=total_reqs,
            covered_requirements_count=covered_count,
            coverage_percentage=coverage_percentage,
            covered_requirements=covered_reqs,
            missing_requirements=missing_reqs,
            mapped_test_cases=mapping,
        )

    def _run_semantic_matching(
        self,
        requirements: List[Requirement],
        testcases: List[TestCase],
        mapping: Dict[str, List[str]],
        threshold: float,
    ) -> int:
        """Executes Phase 2 semantic vector similarity comparison between requirements and test cases.

        Args:
            requirements: List of Requirement models.
            testcases: List of TestCase models.
            mapping: In-out dictionary mapping requirement IDs to list of test case IDs.
            threshold: Cosine similarity threshold.

        Returns:
            Count of new semantic matches added to mapping.
        """
        if self.model is not None and cosine_similarity is not None:
            return self._run_semantic_matching_embeddings(requirements, testcases, mapping, threshold)
        else:
            return self._run_semantic_matching_fallback(requirements, testcases, mapping, threshold)

    def _run_semantic_matching_embeddings(
        self,
        requirements: List[Requirement],
        testcases: List[TestCase],
        mapping: Dict[str, List[str]],
        threshold: float,
    ) -> int:
        """Batch embedding vector comparison for semantic coverage matching."""
        # 1. Prepare requirement embeddings (with caching)
        uncached_reqs = [r for r in requirements if r.id not in self._req_embedding_cache]
        if uncached_reqs:
            req_texts = [r.requirement for r in uncached_reqs]
            try:
                req_embs = self.model.encode(
                    req_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                for r, emb in zip(uncached_reqs, req_embs):
                    self._req_embedding_cache[r.id] = emb
            except Exception as e:
                raise CoverageCheckError(
                    "Embedding failure: Error generating requirement vector embeddings",
                    details=str(e),
                )

        req_matrix = np.array([self._req_embedding_cache[r.id] for r in requirements])

        # 2. Prepare testcase embeddings (with caching)
        uncached_tcs = [tc for tc in testcases if tc.id not in self._tc_embedding_cache]
        if uncached_tcs:
            tc_texts = [tc.get_combined_text() for tc in uncached_tcs]
            try:
                tc_embs = self.model.encode(
                    tc_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                for tc, emb in zip(uncached_tcs, tc_embs):
                    self._tc_embedding_cache[tc.id] = emb
            except Exception as e:
                raise CoverageCheckError(
                    "Embedding failure: Error generating testcase vector embeddings",
                    details=str(e),
                )

        tc_matrix = np.array([self._tc_embedding_cache[tc.id] for tc in testcases])

        # 3. Compute Cosine Similarity Matrix (Requirements x TestCases)
        sim_matrix = cosine_similarity(req_matrix, tc_matrix)

        new_semantic_matches = 0
        for i, req in enumerate(requirements):
            for j, tc in enumerate(testcases):
                score = float(sim_matrix[i][j])
                score = max(0.0, min(1.0, score))

                if score >= threshold:
                    if tc.id not in mapping[req.id]:
                        mapping[req.id].append(tc.id)
                        new_semantic_matches += 1
                        logger.debug(
                            f"Semantic Match: Requirement '{req.id}' matched to Test Case '{tc.id}' "
                            f"(Similarity: {score * 100:.1f}%)."
                        )

        return new_semantic_matches

    def _run_semantic_matching_fallback(
        self,
        requirements: List[Requirement],
        testcases: List[TestCase],
        mapping: Dict[str, List[str]],
        threshold: float,
    ) -> int:
        """Fallback heuristic matching using string distance."""
        new_semantic_matches = 0
        for req in requirements:
            for tc in testcases:
                score = calculate_text_similarity_heuristic(req.requirement, tc.get_combined_text())
                if score >= threshold:
                    if tc.id not in mapping[req.id]:
                        mapping[req.id].append(tc.id)
                        new_semantic_matches += 1
                        logger.debug(
                            f"Semantic Fallback Match: Requirement '{req.id}' matched to Test Case '{tc.id}' "
                            f"(Similarity: {score * 100:.1f}%)."
                        )
        return new_semantic_matches

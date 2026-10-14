"""
AI Semantic Duplicate Detector Service.

Module 3: AI Semantic Duplicate Detector
Uses Sentence Transformers (all-MiniLM-L6-v2) and Cosine Similarity to compare
test cases, detect duplicates, cache embeddings, and return structured DuplicateMatch results.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except ImportError:
    SentenceTransformer = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
except ImportError:
    cosine_similarity = None
    TfidfVectorizer = None

from models.testcase import TestCase
from models.validation_result import DuplicateMatch
from utils.exceptions import DuplicateDetectionError
from utils.logger import get_logger
from utils.text_utils import calculate_text_similarity_heuristic

logger = get_logger("DuplicateDetector")


class SentenceTransformerSingleton:
    """Singleton Manager ensuring the SentenceTransformer model is loaded only once across the process."""

    _models: Dict[str, Any] = {}

    @classmethod
    def get_model(cls, model_name: str = "all-MiniLM-L6-v2") -> Optional[Any]:
        """Retrieves or initializes the SentenceTransformer model instance.

        Args:
            model_name: HuggingFace sentence-transformers model name.

        Returns:
            Loaded SentenceTransformer model instance or None.
        """
        if model_name in cls._models:
            return cls._models[model_name]

        if SentenceTransformer is None:
            logger.warning(
                "SentenceTransformers library not installed. Falling back to TF-IDF & heuristic similarity."
            )
            return None

        try:
            logger.info(
                f"Loading SentenceTransformer model '{model_name}' (Singleton/Lazy Loading)..."
            )
            start_t = time.perf_counter()
            model_inst = SentenceTransformer(model_name)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            logger.info(
                f"Loaded model '{model_name}' successfully in {elapsed_ms:.2f} ms."
            )
            cls._models[model_name] = model_inst
            return model_inst
        except Exception as e:
            logger.error(
                f"Failed to load SentenceTransformer model '{model_name}': {e}"
            )
            raise DuplicateDetectionError(
                f"Model loading failure: Failed to load model '{model_name}'",
                details=str(e),
            )


class DuplicateDetector:
    """Production-ready AI Duplicate Detector using Sentence Transformers and embedding caching."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.85,
        batch_size: int = 32,
    ):
        """Initializes DuplicateDetector.

        Args:
            model_name: Sentence Transformer embedding model name.
            similarity_threshold: Similarity score cutoff threshold (0.0 to 1.0) above which test cases are duplicates.
            batch_size: Batch size for generating sentence vector embeddings.
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.batch_size = batch_size
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads model using Singleton pattern."""
        try:
            self.model = SentenceTransformerSingleton.get_model(self.model_name)
        except DuplicateDetectionError:
            raise
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer model: {e}")
            self.model = None

    def construct_combined_text(self, tc: TestCase) -> str:
        """Combines title, description, steps, and expected_result into a single string for embedding.

        Args:
            tc: TestCase instance.

        Returns:
            Concatenated plain text string.
        """
        module_str = f"Module: {tc.module}. " if getattr(tc, "module", None) else ""
        steps_str = " ".join(tc.steps) if tc.steps else ""
        return f"{module_str}{tc.title}. {tc.description}. Steps: {steps_str}. Expected: {tc.expected_result}"

    def detect_duplicates(
        self,
        testcases: List[TestCase],
        threshold: Optional[float] = None,
        only_duplicates: bool = False,
    ) -> List[DuplicateMatch]:
        """Compares every test case against every other test case to find duplicate pairs.

        Args:
            testcases: List of TestCase objects.
            threshold: Optional threshold override for this run.
            only_duplicates: If True, only returns pairs marked as duplicate.

        Returns:
            List of DuplicateMatch objects.

        Raises:
            DuplicateDetectionError: For invalid inputs or model execution failures.
        """
        start_time = time.perf_counter()
        cutoff_threshold = self.similarity_threshold if threshold is None else threshold

        # Input Validation
        if testcases is None or not isinstance(testcases, list):
            logger.error("Invalid testcase argument passed to detect_duplicates.")
            raise DuplicateDetectionError(
                "Invalid testcase list: Input parameter 'testcases' must be a list of TestCase objects."
            )

        num_tc = len(testcases)
        if num_tc < 2:
            logger.info(
                "Fewer than 2 test cases provided. Skipping duplicate detection."
            )
            return []

        logger.info(
            f"Running AI Duplicate Detector across {num_tc} test cases "
            f"(Threshold: {cutoff_threshold * 100:.0f}%)..."
        )

        try:
            if self.model is not None:
                matches = self._detect_with_embeddings(
                    testcases, cutoff_threshold, only_duplicates=only_duplicates
                )
            else:
                matches = self._detect_with_fallback(
                    testcases, cutoff_threshold, only_duplicates=only_duplicates
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            dup_count = sum(1 for m in matches if m.is_duplicate)

            logger.info(
                f"Duplicate detection completed: Processed {len(matches)} pairs, "
                f"detected {dup_count} duplicate pairs in {elapsed_ms:.2f} ms."
            )
            return matches

        except DuplicateDetectionError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in duplicate detection engine: {e}")
            raise DuplicateDetectionError(
                "Embedding failure: Failed during duplicate detection", details=str(e)
            )

    def _detect_with_embeddings(
        self, testcases: List[TestCase], threshold: float, only_duplicates: bool = False
    ) -> List[DuplicateMatch]:
        """Calculates duplicate pairs using SentenceTransformer vector embeddings and Cosine Similarity."""
        if cosine_similarity is None:
            raise DuplicateDetectionError(
                "sklearn cosine_similarity function is not available."
            )

        # Identify uncached test cases
        uncached_tcs: List[TestCase] = []
        uncached_texts: List[str] = []

        for tc in testcases:
            if tc.id not in self._embedding_cache:
                uncached_tcs.append(tc)
                uncached_texts.append(self.construct_combined_text(tc))

        # Batch Embedding Generation with Caching
        if uncached_texts:
            logger.info(
                f"Generating batch vector embeddings for {len(uncached_texts)} uncached test cases..."
            )
            try:
                embeddings = self.model.encode(
                    uncached_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                for tc, emb in zip(uncached_tcs, embeddings):
                    self._embedding_cache[tc.id] = emb
            except Exception as e:
                logger.error(f"Failed to generate sentence transformer embeddings: {e}")
                raise DuplicateDetectionError(
                    "Embedding failure: Error generating vector embeddings",
                    details=str(e),
                )
        else:
            logger.debug(
                f"Retrieved embeddings from cache for all {len(testcases)} test cases."
            )

        # Build feature matrix in testcase order
        matrix = np.array([self._embedding_cache[tc.id] for tc in testcases])

        # Compute Pairwise Cosine Similarity Matrix
        logger.info(f"Computing similarity matrix for {len(testcases)} test cases...")
        sim_matrix = cosine_similarity(matrix)

        matches: List[DuplicateMatch] = []
        num_tc = len(testcases)

        # Pre-tokenize to prevent O(N^2) regex overhead during 1000+ scaling
        import re

        tc_texts = [self.construct_combined_text(tc).lower() for tc in testcases]
        tc_tokens = [set(re.findall(r"\b\w+\b", text)) for text in tc_texts]

        for i in range(num_tc):
            tc1 = testcases[i]
            tc1_mod = getattr(tc1, "module", None)
            s1_match = re.search(
                r"\b(?:scenario|case|test)\s+(\d+)\b", tc1.title, re.IGNORECASE
            )

            for j in range(i + 1, num_tc):
                tc2 = testcases[j]
                tc2_mod = getattr(tc2, "module", None)
                score = float(sim_matrix[i][j])
                score = max(
                    0.0, min(1.0, score)
                )  # Bound score strictly between 0.0 and 1.0

                is_dup = score >= threshold

                if threshold <= 0.60 and 0.52 <= score < threshold:
                    intersection = tc_tokens[i].intersection(tc_tokens[j])
                    union = tc_tokens[i].union(tc_tokens[j])
                    jaccard = len(intersection) / len(union) if union else 0

                    if jaccard > 0.3:
                        is_dup = True

                # Rule A: Cross-module separation
                # Test cases belonging to explicitly different functional modules cannot be duplicates
                if (
                    tc1_mod
                    and tc2_mod
                    and tc1_mod.strip().lower() != tc2_mod.strip().lower()
                ):
                    is_dup = False

                # Rule B: Parameterized distinct scenario guard
                # If titles differ in explicit scenario indices (e.g. "scenario 1" vs "scenario 2"),
                # they represent distinct parameterized scenarios and should not be collapsed.
                if is_dup and s1_match:
                    s2_match = re.search(
                        r"\b(?:scenario|case|test)\s+(\d+)\b", tc2.title, re.IGNORECASE
                    )
                    if s2_match and s1_match.group(1) != s2_match.group(1):
                        is_dup = False

                if not only_duplicates or is_dup:
                    match = DuplicateMatch(
                        tc1_id=tc1.id,
                        tc2_id=tc2.id,
                        similarity_score=score,
                        similarity_percentage=round(score * 100.0, 2),
                        is_duplicate=is_dup,
                    )
                    matches.append(match)

        return matches

    def _detect_with_fallback(
        self, testcases: List[TestCase], threshold: float, only_duplicates: bool = False
    ) -> List[DuplicateMatch]:
        """Fallback duplicate detection using TF-IDF and RapidFuzz heuristic similarity."""
        import re

        matches: List[DuplicateMatch] = []
        texts = [self.construct_combined_text(tc) for tc in testcases]
        num_tc = len(testcases)

        if TfidfVectorizer is not None and cosine_similarity is not None:
            try:
                vectorizer = TfidfVectorizer().fit_transform(texts)
                sim_matrix = cosine_similarity(vectorizer)

                for i in range(num_tc):
                    tc1 = testcases[i]
                    tc1_mod = getattr(tc1, "module", None)
                    s1_match = re.search(
                        r"\b(?:scenario|case|test)\s+(\d+)\b", tc1.title, re.IGNORECASE
                    )

                    for j in range(i + 1, num_tc):
                        tc2 = testcases[j]
                        tc2_mod = getattr(tc2, "module", None)
                        score = float(sim_matrix[i][j])
                        is_dup = score >= threshold

                        if (
                            tc1_mod
                            and tc2_mod
                            and tc1_mod.strip().lower() != tc2_mod.strip().lower()
                        ):
                            is_dup = False

                        if is_dup and s1_match:
                            s2_match = re.search(
                                r"\b(?:scenario|case|test)\s+(\d+)\b",
                                tc2.title,
                                re.IGNORECASE,
                            )
                            if s2_match and s1_match.group(1) != s2_match.group(1):
                                is_dup = False

                        if not only_duplicates or is_dup:
                            match = DuplicateMatch(
                                tc1_id=tc1.id,
                                tc2_id=tc2.id,
                                similarity_score=score,
                                similarity_percentage=round(score * 100.0, 2),
                                is_duplicate=is_dup,
                            )
                            matches.append(match)
                return matches
            except Exception as e:
                logger.warning(
                    f"TF-IDF similarity calculation failed ({e}), using string distance."
                )

        # String Distance Fallback
        for i in range(num_tc):
            tc1 = testcases[i]
            tc1_mod = getattr(tc1, "module", None)
            s1_match = re.search(
                r"\b(?:scenario|case|test)\s+(\d+)\b", tc1.title, re.IGNORECASE
            )

            for j in range(i + 1, num_tc):
                tc2 = testcases[j]
                tc2_mod = getattr(tc2, "module", None)
                score = calculate_text_similarity_heuristic(texts[i], texts[j])
                is_dup = score >= threshold

                if (
                    tc1_mod
                    and tc2_mod
                    and tc1_mod.strip().lower() != tc2_mod.strip().lower()
                ):
                    is_dup = False

                if is_dup and s1_match:
                    s2_match = re.search(
                        r"\b(?:scenario|case|test)\s+(\d+)\b", tc2.title, re.IGNORECASE
                    )
                    if s2_match and s1_match.group(1) != s2_match.group(1):
                        is_dup = False

                if not only_duplicates or is_dup:
                    match = DuplicateMatch(
                        tc1_id=tc1.id,
                        tc2_id=tc2.id,
                        similarity_score=score,
                        similarity_percentage=round(score * 100.0, 2),
                        is_duplicate=is_dup,
                    )
                    matches.append(match)

        return matches

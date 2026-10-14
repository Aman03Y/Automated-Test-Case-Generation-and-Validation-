"""
Text Utilities Module.

Provides text preprocessing, normalization, sentence splitting, and similarity helpers.
"""

import re
from typing import List
from rapidfuzz import fuzz


def clean_text(text: str) -> str:
    """Normalizes raw input text by stripping extra whitespace and control chars.

    Args:
        text: Input string.

    Returns:
        Cleaned, normalized string.
    """
    if not text:
        return ""
    # Replace multiple spaces, tabs, and newlines with a single space
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def extract_sentences(text: str) -> List[str]:
    """Splits raw text block into individual sentences or bullet points.

    Args:
        text: Multiline string or raw text block.

    Returns:
        List of non-empty extracted sentence/requirement candidates.
    """
    if not text:
        return []

    # First split by explicit line breaks or bullet points / numbered items
    raw_lines = text.splitlines()
    sentences = []

    for line in raw_lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Split further on sentence terminators if line contains multiple sentences
        split_items = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", line_clean)
        for item in split_items:
            item_clean = item.strip()
            if len(item_clean) >= 5:  # Ignore trivial noise
                sentences.append(item_clean)

    return sentences


def calculate_text_similarity_heuristic(text1: str, text2: str) -> float:
    """Calculates rapid string similarity score using rapidfuzz token set/sort ratio.

    Args:
        text1: First string.
        text2: Second string.

    Returns:
        Similarity score float between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0
    sort_score = fuzz.token_sort_ratio(text1.lower(), text2.lower())
    set_score = fuzz.token_set_ratio(text1.lower(), text2.lower())
    best_score = max(sort_score, set_score)
    return round(float(best_score / 100.0), 4)

"""
Requirement Parser & Test Case Loader Service.

Module 1: Requirement Parser (PDF, DOCX, TXT, JSON)
Module 2: Manual Test Case Loader (JSON)
"""

import json
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Union, Optional, Set

try:
    import pymupdf  # type: ignore
except ImportError:
    try:
        import fitz as pymupdf  # type: ignore
    except ImportError:
        pymupdf = None

# Backward compatibility alias
fitz = pymupdf

try:
    import docx  # type: ignore
except ImportError:
    docx = None

try:
    import spacy  # type: ignore
except ImportError:
    spacy = None

try:
    import nltk  # type: ignore
    from nltk.tokenize import sent_tokenize  # type: ignore
except ImportError:
    nltk = None
    sent_tokenize = None

from models.requirement import Requirement
from models.testcase import TestCase
from utils.exceptions import RequirementParseError, TestCaseLoadError
from utils.logger import get_logger
from utils.text_utils import clean_text

logger = get_logger("RequirementParser")


class RequirementParser:
    """Production-grade Requirement Parser extracting functional requirements from PDF, DOCX, TXT, and JSON files."""

    def __init__(
        self,
        req_id_prefix: str = "REQ",
        spacy_model_name: str = "en_core_web_sm",
        min_text_length: int = 8,
    ):
        """Initializes RequirementParser with configurable parameters and NLP models.

        Args:
            req_id_prefix: Prefix used for generating requirement IDs (e.g. REQ).
            spacy_model_name: spaCy language model name for NLP lemmatization.
            min_text_length: Minimum character length for valid requirements.
        """
        self.req_id_prefix = req_id_prefix
        self.spacy_model_name = spacy_model_name
        self.min_text_length = min_text_length
        self._nlp = None
        self._init_nlp()

    def _init_nlp(self) -> None:
        """Lazy initializes spaCy NLP pipeline if available."""
        if spacy is not None and self._nlp is None:
            try:
                self._nlp = spacy.load(self.spacy_model_name)
                logger.debug(f"Loaded spaCy NLP model '{self.spacy_model_name}' successfully.")
            except Exception as e:
                logger.debug(f"Could not load spaCy model '{self.spacy_model_name}': {e}. Using regex/NLTK fallback.")
                self._nlp = None

    def preprocess_nlp_text(
        self,
        text: str,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> str:
        """Applies NLP preprocessing options (tokenization, stopword removal, lemmatization).

        Args:
            text: Input raw text string.
            remove_stopwords: Flag to filter out standard stopwords.
            lemmatize: Flag to convert words to base lemma forms using spaCy.
            lowercase: Flag to convert text to lower case.

        Returns:
            Preprocessed clean text string.
        """
        cleaned = clean_text(text)
        if not cleaned:
            return ""

        if lowercase:
            cleaned = cleaned.lower()

        if self._nlp is not None and (lemmatize or remove_stopwords):
            doc = self._nlp(cleaned)
            tokens = []
            for token in doc:
                if remove_stopwords and token.is_stop:
                    continue
                if token.is_punct and len(token.text) == 1:
                    continue
                word = token.lemma_ if lemmatize else token.text
                tokens.append(word)
            cleaned = " ".join(tokens).strip()

        return cleaned

    def parse_file(
        self,
        file_path: Union[str, Path],
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Parses a requirement file automatically detecting type (.pdf, .docx, .txt, .json).

        Args:
            file_path: Absolute or relative path to document.
            remove_stopwords: Flag for NLP stopword filtering.
            lemmatize: Flag for spaCy lemmatization.
            lowercase: Flag for lowercase normalization.

        Returns:
            List of structured Requirement Pydantic models.

        Raises:
            RequirementParseError: For unsupported format, missing file, corrupted file, or empty content.
        """
        start_time = time.perf_counter()
        path = Path(file_path)

        # Rule 1: Validate file existence
        if not path.exists():
            logger.error(f"Missing requirement file: {file_path}")
            raise RequirementParseError(f"Missing file: Requirement document not found at '{file_path}'")

        if path.is_dir():
            raise RequirementParseError(f"Invalid path: Specified path '{file_path}' is a directory, not a file.")

        ext = path.suffix.lower()
        logger.info(f"Parsing requirement document: {path.name} (Type: {ext})")

        try:
            if ext == ".pdf":
                requirements = self.parse_pdf(path, remove_stopwords, lemmatize, lowercase)
            elif ext == ".docx":
                requirements = self.parse_docx(path, remove_stopwords, lemmatize, lowercase)
            elif ext == ".txt":
                requirements = self.parse_txt(path, remove_stopwords, lemmatize, lowercase)
            elif ext == ".json":
                requirements = self.parse_json(path, remove_stopwords, lemmatize, lowercase)
            else:
                logger.error(f"Unsupported file format: {ext}")
                raise RequirementParseError(f"Unsupported file type: Extension '{ext}' is not supported.")

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"Successfully parsed {len(requirements)} requirements from '{path.name}' "
                f"in {elapsed_ms:.2f} ms."
            )
            return requirements

        except RequirementParseError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error parsing requirement file '{file_path}': {e}")
            raise RequirementParseError(f"Failed to parse document '{file_path}'", details=str(e))

    def parse_pdf(
        self,
        file_path: Path,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Extracts plain text from PDF using PyMuPDF and splits into requirements."""
        if pymupdf is None:
            raise RequirementParseError(
                "PyMuPDF library ('pymupdf') is not installed. Install 'PyMuPDF' to parse PDF files."
            )

        text_blocks = []
        try:
            with pymupdf.open(file_path) as doc:
                if len(doc) == 0:
                    raise RequirementParseError(f"Empty document: PDF file '{file_path.name}' has 0 pages.")

                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text("text")
                    if text:
                        text_blocks.append(text)
        except Exception as e:
            if isinstance(e, RequirementParseError):
                raise
            raise RequirementParseError(f"Corrupted PDF: Failed to read unreadable PDF file '{file_path.name}'", details=str(e))

        full_text = "\n".join(text_blocks).strip()
        if not full_text:
            raise RequirementParseError(f"Empty document: PDF file '{file_path.name}' contains no readable text.")

        return self._process_raw_text(full_text, remove_stopwords, lemmatize, lowercase)

    def parse_docx(
        self,
        file_path: Path,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Extracts plain text from DOCX using python-docx and splits into requirements."""
        if docx is None:
            raise RequirementParseError(
                "python-docx library is not installed. Install 'python-docx' to parse DOCX files."
            )

        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            # Also extract table text if present
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                    if row_text:
                        paragraphs.append(row_text)
        except Exception as e:
            raise RequirementParseError(f"Corrupted DOCX: Failed to read unreadable Word file '{file_path.name}'", details=str(e))

        full_text = "\n".join(paragraphs).strip()
        if not full_text:
            raise RequirementParseError(f"Empty document: DOCX file '{file_path.name}' contains no readable text.")

        return self._process_raw_text(full_text, remove_stopwords, lemmatize, lowercase)

    def parse_txt(
        self,
        file_path: Path,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Reads plain text file and splits into requirements."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_text = f.read()
        except Exception as e:
            raise RequirementParseError(f"Failed to read TXT file '{file_path.name}'", details=str(e))

        if not full_text.strip():
            raise RequirementParseError(f"Empty document: TXT file '{file_path.name}' is empty.")

        return self._process_raw_text(full_text, remove_stopwords, lemmatize, lowercase)

    def parse_json(
        self,
        file_path: Union[str, Path],
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Parses structured requirements JSON file."""
        path = Path(file_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RequirementParseError(f"JSON parsing failure: Invalid JSON format in '{path.name}'", details=str(e))
        except Exception as e:
            raise RequirementParseError(f"Failed to read JSON file '{path.name}'", details=str(e))

        if not data:
            raise RequirementParseError(f"Empty document: JSON file '{path.name}' is empty or contains no data.")

        if not isinstance(data, list):
            raise RequirementParseError("JSON parsing failure: Top-level JSON structure must be a list of requirement objects.")

        requirements: List[Requirement] = []
        seen_texts: Set[str] = set()

        for idx, item in enumerate(data, start=1):
            req_text = ""
            category = None
            explicit_id = None

            if isinstance(item, str):
                req_text = item
            elif isinstance(item, dict):
                explicit_id = item.get("id")
                req_text = item.get("requirement") or item.get("description") or item.get("text", "")
                category = item.get("category")

            req_text_clean = clean_text(req_text)
            if not req_text_clean or len(req_text_clean) < self.min_text_length:
                continue

            processed_text = self.preprocess_nlp_text(
                req_text_clean, remove_stopwords=remove_stopwords, lemmatize=lemmatize, lowercase=lowercase
            )

            # Deduplication check
            norm_key = processed_text.lower()
            if norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)

            req_id = explicit_id if explicit_id else f"{self.req_id_prefix}-{len(requirements)+1:03d}"
            requirements.append(Requirement(id=req_id, requirement=processed_text, category=category))

        if not requirements:
            raise RequirementParseError(f"Empty document: No valid requirements extracted from '{file_path.name}'.")

        return requirements

    def _process_raw_text(
        self,
        text: str,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        lowercase: bool = False,
    ) -> List[Requirement]:
        """Splits raw unstructured text into individual functional requirement models with deduplication."""
        cleaned = clean_text(text)
        if not cleaned:
            raise RequirementParseError("Empty document: Document contains no text.")

        candidate_statements: List[str] = []

        # Check for explicit requirement ID format (e.g. REQ-001: Customer can login)
        pattern = r"(?:(?:\bREQ-\d+\b|\bREQUIREMENT\s*\d+\b|\[REQ-\d+\]):?\s*)(.*?)(?=(?:\bREQ-\d+\b|\bREQUIREMENT\s*\d+\b|\[REQ-\d+\]):?|$)"
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

        if matches and len(matches) > 1:
            for match in matches:
                candidate_statements.append(clean_text(match))
        else:
            # Tokenize into individual sentences
            if sent_tokenize is not None:
                sentences = sent_tokenize(text)
            else:
                sentences = text.splitlines()

            for stmt in sentences:
                clean_stmt = clean_text(stmt)
                if clean_stmt:
                    candidate_statements.append(clean_stmt)

        requirements: List[Requirement] = []
        seen_texts: Set[str] = set()

        for stmt in candidate_statements:
            if not stmt or len(stmt) < self.min_text_length:
                continue

            processed = self.preprocess_nlp_text(
                stmt, remove_stopwords=remove_stopwords, lemmatize=lemmatize, lowercase=lowercase
            )
            if not processed:
                continue

            # Deduplication
            norm_key = processed.lower()
            if norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)

            req_id = f"{self.req_id_prefix}-{len(requirements)+1:03d}"
            requirements.append(Requirement(id=req_id, requirement=processed))

        if not requirements:
            raise RequirementParseError("Empty document: Failed to extract valid functional requirements.")

        return requirements


from services.testcase_loader import TestCaseLoader

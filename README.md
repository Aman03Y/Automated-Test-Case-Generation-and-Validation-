# AI-Based Automated Test Case Validation System

An enterprise-grade, local AI backend engine built in Python to validate manually written software test cases against software requirements specifications.

It automatically detects **duplicate test cases**, flags **missing test scenarios**, measures **requirement coverage**, evaluates **test case quality and formatting rules**, and generates structured **validation reports**.

---

## 🌟 Key Features

1. **Multi-Format Requirement Parsing (`Module 1`)**
   - Extracts functional requirements from **PDF** (`PyMuPDF`), **DOCX** (`python-docx`), **TXT**, and **JSON** files.
   - Cleans unstructured text and extracts structured requirement models (`REQ-001`, `REQ-002`, etc.).

2. **Manual Test Case Loader (`Module 2`)**
   - Parses manual test case datasets from JSON files into validated Pydantic data models.

3. **AI Semantic Duplicate Detector (`Module 3`)**
   - Utilizes local Sentence Transformers (`all-MiniLM-L6-v2`) and Cosine Similarity to compute semantic embeddings across all test cases.
   - Flag duplicate test cases exceeding the configurable similarity threshold (default: `85%`).

4. **Requirement Coverage Checker (`Module 4`)**
   - Compares requirements against manual test cases using explicit requirement mappings and semantic matching.
   - Identifies untested requirements, covered count, and calculates exact coverage percentage.

5. **Rule-Based Validation Engine (`Module 5`)**
   - Evaluates every test case against 7 strict quality compliance rules:
     1. Title exists & non-empty
     2. Description exists & non-empty
     3. Minimum one step present
     4. Expected result exists & non-empty
     5. Priority exists & valid (`High`, `Medium`, `Low`, `Critical`)
     6. Requirement mapped to valid requirement specification
     7. Duplicate detection check
   - Categorizes outcomes into `PASS`, `WARNING`, or `FAIL` status with diagnostic messages.

6. **Weighted Quality Score Engine (`Module 6`)**
   - Generates an overall quality score from **0 to 100** using weighted components:
     - **Requirement Coverage**: `40%`
     - **Test Case Completeness**: `25%`
     - **Duplicate Absence**: `20%`
     - **Formatting Quality**: `15%`

7. **Structured Report Generator (`Module 7`)**
   - Generates JSON and Markdown reports in `outputs/` folder matching target schema:
     ```json
     {
         "coverage": 95.0,
         "duplicates": 2,
         "quality_score": 91.0,
         "missing_requirements": [...],
         "failed_testcases": [...]
     }
     ```

---

## 📁 Project Architecture & Directory Structure

```
ai_testcase_validator/
│
├── data/                      # Input sample datasets
│   ├── requirements/          # Requirement files (.json, .txt, .docx, .pdf)
│   │   ├── sample_requirements.json
│   │   └── sample_requirements.txt
│   └── testcases/             # Test case datasets (.json)
│       └── sample_testcases.json
│
├── models/                    # Pydantic & Data Models
│   ├── requirement.py         # Requirement model
│   ├── testcase.py            # TestCase model & Priority enum
│   ├── validation_result.py   # Status, DuplicateMatch & CoverageResult models
│   └── report.py              # QualityBreakdown & ValidationReport models
│
├── services/                  # Core Business & AI Logic Services
│   ├── parser.py              # Requirement parser & testcase loader
│   ├── duplicate_detector.py  # SentenceTransformer duplicate detector
│   ├── coverage_checker.py    # Requirement coverage & mapping checker
│   ├── validator.py           # 7-rule validation engine
│   ├── quality_score.py       # Weighted quality scoring engine (40/25/20/15)
│   └── report_generator.py    # JSON and Markdown report generator
│
├── utils/                     # Cross-Cutting Utility Modules
│   ├── logger.py              # Centralized logging configuration
│   ├── text_utils.py          # Preprocessing & string comparison helpers
│   └── exceptions.py          # Custom exception classes
│
├── outputs/                   # Destination for generated validation reports
│
├── tests/                     # Pytest Unit Test Suite
│   ├── test_parser.py
│   ├── test_duplicate_detector.py
│   ├── test_coverage_checker.py
│   ├── test_validator.py
│   ├── test_quality_score.py
│   └── test_report_generator.py
│
├── main.py                    # Complete end-to-end pipeline CLI runner
├── requirements.txt           # Python dependencies
└── README.md                  # System Documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python 3.12+** installed on your system.

### 1. Clone / Navigate to Project Directory
```bash
cd ai_testcase_validator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage Guide

### Running the End-to-End Workflow (`main.py`)
Run the pipeline on default sample dataset:
```bash
python main.py
```

### Custom Files & Threshold Arguments
```bash
python main.py --requirements data/requirements/sample_requirements.json \
                --testcases data/testcases/sample_testcases.json \
                --output-dir outputs \
                --threshold 0.85
```

---

## 🧪 Running Unit Tests

Run the complete automated test suite using `pytest`:
```bash
pytest tests/ -v
```

---

## 📊 Sample JSON Output Report

Located at `outputs/validation_report.json`:

```json
{
    "coverage": 80.0,
    "duplicates": 1,
    "quality_score": 83.33,
    "missing_requirements": [
        "REQ-005"
    ],
    "failed_testcases": [
        {
            "id": "TC005",
            "title": "Incomplete Profile Update Test",
            "status": "FAIL",
            "errors": [
                "Rule Failed: Description is missing or empty.",
                "Rule Failed: Test case must contain at least one step.",
                "Rule Failed: Expected result is missing or empty."
            ],
            "warnings": [
                "Warning: Test case is not mapped to any requirement ID."
            ]
        }
    ],
    "score_breakdown": {
        "coverage_score_max_40": 32.0,
        "completeness_score_max_25": 20.83,
        "duplicate_score_max_20": 16.67,
        "formatting_score_max_15": 13.83,
        "overall_score": 83.33
    }
}
```

---

## 🗺️ Roadmap: Extending to FastAPI

This project is built using a clean, decoupled architecture. To extend it into a FastAPI backend:
1. Import services directly (`RequirementParser`, `DuplicateDetector`, `CoverageChecker`, `ValidationEngine`, `QualityScoreCalculator`, `ReportGenerator`).
2. Add API endpoints (`POST /api/v1/validate`, `POST /api/v1/parse-requirements`, `POST /api/v1/detect-duplicates`).
3. Reuse existing Pydantic models from `models/` for API request/response schemas.

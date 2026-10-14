"""
Unit Tests for FastAPI REST API Endpoints (Phase 8).
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.dependencies import state

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_app_state():
    """Resets in-memory app state before each API test."""
    state.clear()
    yield
    state.clear()


def test_root_health_check():
    """Tests GET / health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs_url" in data


def test_upload_requirements_json(tmp_path: Path):
    """Tests POST /api/requirements/upload with JSON file."""
    req_data = [
        {"id": "REQ-001", "requirement": "User login functionality requirement."},
        {"id": "REQ-002", "requirement": "User logout functionality requirement."},
    ]
    json_file = tmp_path / "reqs.json"
    json_file.write_text(json.dumps(req_data), encoding="utf-8")

    with open(json_file, "rb") as f:
        response = client.post("/api/requirements/upload", files={"file": ("reqs.json", f, "application/json")})

    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 2
    assert len(data["requirements"]) == 2


def test_upload_requirements_invalid_ext(tmp_path: Path):
    """Tests POST /api/requirements/upload with unsupported file extension."""
    invalid_file = tmp_path / "reqs.csv"
    invalid_file.write_text("id,text\nREQ-001,Text", encoding="utf-8")

    with open(invalid_file, "rb") as f:
        response = client.post("/api/requirements/upload", files={"file": ("reqs.csv", f, "text/csv")})

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_testcases_json(tmp_path: Path):
    """Tests POST /api/testcases/upload with test cases JSON file."""
    tc_data = [
        {
            "id": "TC001",
            "title": "User Login Test",
            "description": "Verify user can log into system with valid credentials.",
            "steps": ["Step 1 open page", "Step 2 enter credentials"],
            "expected_result": "Dashboard displayed successfully.",
            "priority": "High",
            "requirement_ids": ["REQ-001"],
        }
    ]
    tc_file = tmp_path / "testcases.json"
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")

    with open(tc_file, "rb") as f:
        response = client.post("/api/testcases/upload", files={"file": ("testcases.json", f, "application/json")})

    assert response.status_code == 201
    data = response.json()
    assert data["count"] == 1
    assert data["testcases"][0]["id"] == "TC001"


def test_run_validation_pipeline_endpoint(tmp_path: Path):
    """Tests POST /api/validate endpoint executing full AI pipeline."""
    # 1. Upload Requirements
    req_data = [{"id": "REQ-001", "requirement": "User login functionality requirement."}]
    req_file = tmp_path / "reqs.json"
    req_file.write_text(json.dumps(req_data), encoding="utf-8")
    with open(req_file, "rb") as f:
        client.post("/api/requirements/upload", files={"file": ("reqs.json", f, "application/json")})

    # 2. Upload Test Cases
    tc_data = [
        {
            "id": "TC001",
            "title": "User Login Test",
            "description": "Verify user can log into system with valid credentials.",
            "steps": ["Step 1 open page"],
            "expected_result": "Dashboard displayed successfully.",
            "priority": "High",
            "requirement_ids": ["REQ-001"],
        }
    ]
    tc_file = tmp_path / "testcases.json"
    tc_file.write_text(json.dumps(tc_data), encoding="utf-8")
    with open(tc_file, "rb") as f:
        client.post("/api/testcases/upload", files={"file": ("testcases.json", f, "application/json")})

    # 3. Run Validation Pipeline
    val_resp = client.post("/api/validate")
    assert val_resp.status_code == 200
    report_data = val_resp.json()
    assert report_data["coverage"] == 100.0
    assert "quality_score" in report_data
    assert "recommendations" in report_data


def test_get_report_json_endpoint(tmp_path: Path):
    """Tests GET /api/report/json endpoint."""
    test_run_validation_pipeline_endpoint(tmp_path)
    resp = client.get("/api/report/json")
    assert resp.status_code == 200


def test_get_report_pdf_endpoint(tmp_path: Path):
    """Tests GET /api/report/pdf endpoint."""
    test_run_validation_pipeline_endpoint(tmp_path)
    resp = client.get("/api/report/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_get_report_markdown_endpoint(tmp_path: Path):
    """Tests GET /api/report/markdown endpoint."""
    test_run_validation_pipeline_endpoint(tmp_path)
    resp = client.get("/api/report/markdown")
    assert resp.status_code == 200
    assert "content-type" in resp.headers


def test_get_recommendations_endpoint(tmp_path: Path):
    """Tests GET /api/recommendations endpoint."""
    test_run_validation_pipeline_endpoint(tmp_path)
    resp = client.get("/api/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "testcase_recommendations" in data


def test_get_traceability_matrix_endpoint(tmp_path: Path):
    """Tests GET /api/traceability-matrix endpoint."""
    test_run_validation_pipeline_endpoint(tmp_path)
    resp = client.get("/api/traceability-matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert "matrix" in data
    assert data["total_requirements"] == 1

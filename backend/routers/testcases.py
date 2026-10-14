"""FastAPI Router for Test Cases Upload and Validation."""

from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status

from backend.config import settings
from backend.dependencies import get_app_state, AppState
from backend.schemas.api_schemas import TestCaseUploadResponse, AutoFixResponse
from services.testcase_loader import TestCaseLoader
from backend.routers.validation import validate_tests

router = APIRouter(prefix="/api/testcases", tags=["Test Cases"])


@router.post(
    "/upload",
    response_model=TestCaseUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload manual test cases JSON file",
)
async def upload_testcases(
    file: UploadFile = File(...),
    app_state: AppState = Depends(get_app_state),
):
    """Accepts JSON file upload of test cases and stores them in session app state."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext != ".json":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Expected .json.",
        )

    temp_path = settings.upload_dir / file.filename
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        loader = TestCaseLoader(strict=False)
        testcases = loader.load_json(temp_path)
        app_state.testcases = testcases
        return TestCaseUploadResponse(
            message=f"Successfully uploaded and parsed {len(testcases)} test cases.",
            count=len(testcases),
            testcases=testcases,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate-tests", response_model=AutoFixResponse, summary="Validate and fix test cases")
async def route_validate_tests(file: UploadFile = File(...)):
    """Validates, deduplicates, and sanitizes test cases uploaded in JSON format."""
    return await validate_tests(file)

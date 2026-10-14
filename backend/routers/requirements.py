"""
FastAPI Router for Requirement Document Upload and Parsing.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.config import settings
from backend.dependencies import AppState, get_app_state
from backend.schemas.api_schemas import ErrorResponse, RequirementUploadResponse
from services.parser import RequirementParser
from utils.exceptions import RequirementParseError
from utils.logger import get_logger

logger = get_logger("API_Requirements")
router = APIRouter(prefix="/api/requirements", tags=["Requirements"])


@router.post(
    "/upload",
    response_model=RequirementUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse software requirement document (.pdf, .docx, .txt, .json)",
)
async def upload_requirements(
    file: UploadFile = File(...),
    app_state: AppState = Depends(get_app_state),
):
    """Accepts PDF, DOCX, TXT, or JSON file upload and extracts structured Requirement models."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt", ".json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Expected .pdf, .docx, .txt, or .json.",
        )

    # Save temp file
    temp_path = settings.upload_dir / file.filename
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved uploaded requirement file to: {temp_path.resolve()}")

        # Parse using RequirementParser
        parser = RequirementParser()
        parsed_reqs = parser.parse_file(temp_path)

        app_state.requirements = parsed_reqs

        return RequirementUploadResponse(
            message=f"Successfully parsed {len(parsed_reqs)} requirements from '{file.filename}'.",
            filename=file.filename,
            count=len(parsed_reqs),
            requirements=parsed_reqs,
        )

    except RequirementParseError as e:
        logger.error(f"Requirement parsing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error during requirement file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.schemas.api_schemas import GenerateTestCasesResponse
from models.testcase import TestCase
from services.testcase_generator import TestCaseGenerator


class LegacyGenerateBody(BaseModel):
    cases_per_requirement: int = Field(default=3, ge=1, le=5)
    include_negative: bool = True
    include_boundary: bool = True
    include_edge: bool = True
    include_security: bool = False
    strategy: Literal["comprehensive", "minimal"] = "comprehensive"


@router.post(
    "/generate-testcases",
    response_model=GenerateTestCasesResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Test Cases from parsed requirements (upgraded: multi-variant generator)",
)
async def generate_testcases_endpoint(
    body: Optional[LegacyGenerateBody] = None,
    app_state: AppState = Depends(get_app_state),
):
    if not app_state.requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No requirements loaded to generate test cases.",
        )
    opts = body or LegacyGenerateBody()
    gen = TestCaseGenerator()
    generated_tcs = gen.generate(
        requirements=app_state.requirements,
        cases_per_requirement=opts.cases_per_requirement,
        include_negative=opts.include_negative,
        include_boundary=opts.include_boundary,
        include_edge=opts.include_edge,
        include_security=opts.include_security,
        strategy=opts.strategy,
    )
    app_state.testcases = generated_tcs
    return GenerateTestCasesResponse(
        message=f"Generated {len(generated_tcs)} test cases from {len(app_state.requirements)} requirements ({opts.cases_per_requirement} per req).",
        count=len(generated_tcs),
        testcases=generated_tcs,
    )

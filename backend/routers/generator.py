"""
FastAPI Router for AI Test Case Generation.

Exposes the intelligent TestCaseGenerator (services/testcase_generator.py)
as REST endpoints. Complements the existing validation pipeline.
"""

import json
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from backend.config import settings
from backend.dependencies import AppState, get_app_state
from backend.schemas.api_schemas import ErrorResponse, GenerateTestCasesResponse
from models.requirement import Requirement
from models.testcase import TestCase
from services.parser import RequirementParser
from services.testcase_generator import TestCaseGenerator
from utils.logger import get_logger

logger = get_logger("API_Generator")
router = APIRouter(prefix="/api/generator", tags=["Test Case Generator"])


# ---- Request / Response Schemas ----


class GenerateRequest(BaseModel):
    """Inline generation request - generates from provided requirements list."""

    requirements: Optional[List[Requirement]] = Field(
        default=None,
        description="Optional inline requirements; if omitted, uses session requirements from /api/requirements/upload",
    )
    cases_per_requirement: int = Field(
        default=3, ge=1, le=5, description="Number of variants per requirement (1-5)"
    )
    include_negative: bool = Field(default=True)
    include_boundary: bool = Field(default=True)
    include_edge: bool = Field(default=True)
    include_security: bool = Field(default=False)
    include_performance: bool = Field(default=False)
    strategy: Literal["comprehensive", "minimal"] = Field(default="comprehensive")
    requirement_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional filter: only generate for these requirement IDs",
    )
    id_prefix: str = Field(default="TC-GEN")
    save_to_session: bool = Field(
        default=True,
        description="If true, stores results in app_state.testcases for immediate validation",
    )


class GenerateResponse(BaseModel):
    message: str
    count: int
    cases_per_requirement: int
    strategy: str
    requirements_covered: int
    testcases: List[TestCase]
    # Also include raw dicts for frontend convenience
    testcases_dict: Optional[List[dict]] = None


def _get_requirements_for_generation(
    app_state: AppState,
    inline_requirements: Optional[List[Requirement]],
    requirement_ids: Optional[List[str]],
) -> List[Requirement]:
    if inline_requirements is not None and len(inline_requirements) > 0:
        reqs = inline_requirements
    elif app_state.requirements:
        reqs = app_state.requirements
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No requirements available. Upload requirements via /api/requirements/upload or provide inline requirements in the request body.",
        )
    if requirement_ids:
        id_set = set(requirement_ids)
        filtered = [r for r in reqs if r.id in id_set]
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No matching requirement_ids found. Provided: {requirement_ids}",
            )
        return filtered
    return reqs


def _run_generator(
    requirements: List[Requirement],
    cases_per_requirement: int,
    include_negative: bool,
    include_boundary: bool,
    include_edge: bool,
    include_security: bool,
    include_performance: bool,
    strategy: str,
    id_prefix: str,
) -> List[TestCase]:
    gen = TestCaseGenerator()
    return gen.generate(
        requirements=requirements,
        cases_per_requirement=cases_per_requirement,
        include_negative=include_negative,
        include_boundary=include_boundary,
        include_edge=include_edge,
        include_security=include_security,
        include_performance=include_performance,
        strategy=strategy,
        id_prefix=id_prefix,
    )


@router.post(
    "",
    response_model=GenerateResponse,
    summary="Generate test cases from session requirements (uploaded via /api/requirements/upload)",
)
@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate test cases from session requirements (alias)",
)
async def generate_from_session(
    payload: Optional[GenerateRequest] = None,
    app_state: AppState = Depends(get_app_state),
):
    """
    Generates comprehensive test cases from the requirements previously uploaded
    to the session (POST /api/requirements/upload). Optionally filters to a subset
    and controls variant types via the payload.

    If payload.requirements is provided, those inline requirements are used instead.
    """
    if payload is None:
        payload = GenerateRequest()

    reqs = _get_requirements_for_generation(
        app_state, payload.requirements, payload.requirement_ids
    )

    tcs = _run_generator(
        requirements=reqs,
        cases_per_requirement=payload.cases_per_requirement,
        include_negative=payload.include_negative,
        include_boundary=payload.include_boundary,
        include_edge=payload.include_edge,
        include_security=payload.include_security,
        include_performance=payload.include_performance,
        strategy=payload.strategy,
        id_prefix=payload.id_prefix,
    )

    if payload.save_to_session:
        app_state.testcases = tcs

    return GenerateResponse(
        message=f"Generated {len(tcs)} test cases from {len(reqs)} requirements ({payload.cases_per_requirement} per req, strategy={payload.strategy}).",
        count=len(tcs),
        cases_per_requirement=payload.cases_per_requirement,
        strategy=payload.strategy,
        requirements_covered=len(reqs),
        testcases=tcs,
        testcases_dict=[tc.to_dict() for tc in tcs],
    )


@router.post(
    "/upload-and-generate",
    response_model=GenerateResponse,
    summary="One-shot: upload requirement file and generate test cases",
)
async def upload_and_generate(
    file: UploadFile = File(
        ..., description="Requirement file (.pdf, .docx, .txt, .json)"
    ),
    cases_per_requirement: int = Form(default=3, ge=1, le=5),
    include_negative: bool = Form(default=True),
    include_boundary: bool = Form(default=True),
    include_edge: bool = Form(default=True),
    include_security: bool = Form(default=False),
    include_performance: bool = Form(default=False),
    strategy: str = Form(default="comprehensive"),
    id_prefix: str = Form(default="TC-GEN"),
    app_state: AppState = Depends(get_app_state),
):
    """Uploads a requirement document, parses it, then immediately generates test cases."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided."
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt", ".json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Use .pdf, .docx, .txt, or .json.",
        )

    if strategy not in {"comprehensive", "minimal"}:
        raise HTTPException(
            status_code=400, detail="strategy must be 'comprehensive' or 'minimal'."
        )

    # Save temp file
    temp_path = settings.upload_dir / file.filename
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        parser = RequirementParser()
        parsed_reqs = parser.parse_file(temp_path)
        app_state.requirements = parsed_reqs

        tcs = _run_generator(
            requirements=parsed_reqs,
            cases_per_requirement=cases_per_requirement,
            include_negative=include_negative,
            include_boundary=include_boundary,
            include_edge=include_edge,
            include_security=include_security,
            include_performance=include_performance,
            strategy=strategy,
            id_prefix=id_prefix,
        )
        app_state.testcases = tcs

        return GenerateResponse(
            message=f"Parsed {len(parsed_reqs)} requirements and generated {len(tcs)} test cases.",
            count=len(tcs),
            cases_per_requirement=cases_per_requirement,
            strategy=strategy,
            requirements_covered=len(parsed_reqs),
            testcases=tcs,
            testcases_dict=[tc.to_dict() for tc in tcs],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in upload-and-generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/preview",
    response_model=GenerateResponse,
    summary="Preview generation (does NOT save to session)",
)
async def preview_generation(
    payload: GenerateRequest,
    app_state: AppState = Depends(get_app_state),
):
    """Preview generated test cases without persisting to session state."""
    reqs = _get_requirements_for_generation(
        app_state, payload.requirements, payload.requirement_ids
    )
    tcs = _run_generator(
        requirements=reqs,
        cases_per_requirement=payload.cases_per_requirement,
        include_negative=payload.include_negative,
        include_boundary=payload.include_boundary,
        include_edge=payload.include_edge,
        include_security=payload.include_security,
        include_performance=payload.include_performance,
        strategy=payload.strategy,
        id_prefix=payload.id_prefix,
    )
    return GenerateResponse(
        message=f"Preview: {len(tcs)} test cases from {len(reqs)} requirements.",
        count=len(tcs),
        cases_per_requirement=payload.cases_per_requirement,
        strategy=payload.strategy,
        requirements_covered=len(reqs),
        testcases=tcs,
        testcases_dict=[tc.to_dict() for tc in tcs],
    )


@router.get(
    "/options",
    summary="Get available generation options and defaults",
)
async def get_generation_options():
    return {
        "cases_per_requirement": {"default": 3, "min": 1, "max": 5},
        "strategies": ["comprehensive", "minimal"],
        "toggles": {
            "include_negative": {
                "default": True,
                "description": "Invalid / incorrect input handling",
            },
            "include_boundary": {
                "default": True,
                "description": "Boundary & limit value checks",
            },
            "include_edge": {
                "default": True,
                "description": "Edge cases / empty states",
            },
            "include_security": {
                "default": False,
                "description": "Auth / authorization checks",
            },
            "include_performance": {
                "default": False,
                "description": "Load & timing checks",
            },
        },
        "test_types_generated": [
            "positive",
            "negative",
            "boundary",
            "edge",
            "security",
            "performance",
        ],
        "id_prefix": {"default": "TC-GEN"},
    }

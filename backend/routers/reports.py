"""
FastAPI Router for Reports, Recommendations, and Traceability Matrix Downloads.
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse, JSONResponse
from backend.config import settings
from backend.dependencies import get_app_state, AppState
from utils.logger import get_logger

logger = get_logger("API_Reports")
router = APIRouter(prefix="/api", tags=["Reports & Analytics"])


@router.get(
    "/report/json",
    summary="Get validation report as JSON payload or file",
)
async def get_report_json(app_state: AppState = Depends(get_app_state)):
    """Returns the generated validation report in JSON format."""
    json_file = settings.output_dir / "validation_report.json"
    if not json_file.exists():
        if app_state.last_report:
            return app_state.last_report.to_dict()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation report JSON not found. Please run /api/validate first.",
        )

    return FileResponse(
        path=json_file,
        media_type="application/json",
        filename="validation_report.json",
    )


@router.get(
    "/report/pdf",
    summary="Download validation report as PDF",
)
async def get_report_pdf():
    """Returns the generated validation report as a downloadable PDF document."""
    pdf_file = settings.output_dir / "validation_report.pdf"
    if not pdf_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file not found. Please run /api/validate first.",
        )

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename="validation_report.pdf",
    )


@router.get(
    "/report/markdown",
    summary="Download validation report as Markdown",
)
async def get_report_markdown():
    """Returns the generated validation report in Markdown format."""
    md_file = settings.output_dir / "validation_report.md"
    if not md_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Markdown report file not found. Please run /api/validate first.",
        )

    return FileResponse(
        path=md_file,
        media_type="text/markdown",
        filename="validation_report.md",
    )


@router.get(
    "/recommendations",
    summary="Get AI recommendations for project and test cases",
)
async def get_recommendations(app_state: AppState = Depends(get_app_state)):
    """Returns structured AI recommendations generated for test cases and missing requirements."""
    if app_state.last_report and app_state.last_report.recommendations:
        return app_state.last_report.recommendations

    json_file = settings.output_dir / "validation_report.json"
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("recommendations", {})
        except Exception as e:
            logger.error(f"Error reading recommendations from {json_file}: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Recommendations not found. Please run /api/validate first.",
    )


@router.get(
    "/traceability-matrix",
    summary="Get Requirement Traceability Matrix (RTM)",
)
async def get_traceability_matrix(app_state: AppState = Depends(get_app_state)):
    """Returns the Requirement Traceability Matrix (RTM) JSON payload."""
    if app_state.last_rtm:
        return app_state.last_rtm

    rtm_file = settings.output_dir / "traceability_matrix.json"
    if rtm_file.exists():
        try:
            with open(rtm_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading RTM JSON from {rtm_file}: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Requirement Traceability Matrix (RTM) not found. Please run /api/validate first.",
    )

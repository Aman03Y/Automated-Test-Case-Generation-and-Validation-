"""
FastAPI Backend Application Entry Point.

AI-Based Automated Test Case Validation System REST API.
Enables Swagger UI (/docs) and OpenAPI specs (/openapi.json).
"""

import logging
import warnings

# Suppress deprecation and third-party library warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress verbose external loggers to maintain clean console output
for noisy_logger in [
    "uvicorn.access",
    "uvicorn.error",
    "transformers",
    "sentence_transformers",
    "torch",
    "filelock",
    "huggingface_hub",
    "urllib3",
    "multipart",
    "asyncio",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.routers.testcases import router as testcases_router
from utils.exceptions import (
    CoverageCheckError,
    DuplicateDetectionError,
    ReportGenerationError,
    RequirementParseError,
    TestCaseLoadError,
    ValidationError,
)
from utils.logger import setup_logger

logger = setup_logger("API_Server")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-grade REST API for automated software test case validation against software requirements. "
        "Detects duplicates, checks coverage, evaluates quality rules, generates scores, and exports PDF/JSON/Markdown reports."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

from backend.routers import (
    generator_router,
    reports_router,
    requirements_router,
    testcases_router,
    validation_router,
)

# Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(requirements_router)
app.include_router(testcases_router)
app.include_router(validation_router)
app.include_router(reports_router)
app.include_router(generator_router)


# Global Exception Handlers
@app.exception_handler(RequirementParseError)
async def requirement_parse_exception_handler(
    request: Request, exc: RequirementParseError
):
    logger.error(f"RequirementParseError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Requirement Parsing Error", "details": str(exc)},
    )


@app.exception_handler(TestCaseLoadError)
async def testcase_load_exception_handler(request: Request, exc: TestCaseLoadError):
    logger.error(f"TestCaseLoadError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Test Case Loading Error", "details": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"ValidationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Test Case Rule Validation Error", "details": str(exc)},
    )


@app.get("/", summary="Root Health Check")
async def root():
    """Health check endpoint returning system status and Swagger UI link."""
    return {
        "status": "online",
        "system": settings.app_name,
        "version": settings.app_version,
        "docs_url": "/docs",
        "openapi_spec": "/openapi.json",
    }


@app.get("/api/health", summary="API Health Probe")
async def api_health():
    """Lightweight probe used by frontend to detect if backend is reachable."""
    return {"status": "ok"}


@app.get("/health", summary="Health Probe (alt)")
async def health():
    return {"status": "ok"}

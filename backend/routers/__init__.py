"""FastAPI Routers Initialization."""

from .generator import router as generator_router
from .reports import router as reports_router
from .requirements import router as requirements_router
from .testcases import router as testcases_router
from .validation import router as validation_router

__all__ = [
    "requirements_router",
    "testcases_router",
    "validation_router",
    "reports_router",
    "generator_router",
]

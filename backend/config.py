"""
FastAPI Backend Configuration.
"""

from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    """API System Settings."""

    app_name: str = "AI-Based Automated Test Case Validation System API"
    app_version: str = "1.0.0"
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")


settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)

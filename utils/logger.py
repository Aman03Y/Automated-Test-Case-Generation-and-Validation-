"""
Logging Configuration Module.

Provides centralized logging across all modules in the AI Test Case Validator.
"""

import logging
import os
import sys
from typing import Optional


def get_default_log_level() -> int:
    """Returns logging level configured by LOG_LEVEL env var, defaulting to WARNING for clean output."""
    env_level = os.getenv("LOG_LEVEL", "WARNING").strip().upper()
    return getattr(logging, env_level, logging.WARNING)


def setup_logger(
    name: str = "ai_testcase_validator",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configures and returns a logger instance with standardized formatting.

    Args:
        name: Name of the logger instance.
        level: Optional logging level. If None, defaults to LOG_LEVEL env var (default: WARNING).
        log_file: Optional file path to direct log output.

    Returns:
        logging.Logger: Configured logger instance.
    """
    effective_level = get_default_log_level() if level is None else level
    logger = logging.getLogger(name)
    logger.setLevel(effective_level)

    # Prevent duplicate handlers if logger is configured multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional File Handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ai_testcase_validator") -> logging.Logger:
    """Retrieves an existing logger or initializes a default one.

    Args:
        name: Name of the logger instance.

    Returns:
        logging.Logger: Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    logger.setLevel(get_default_log_level())
    return logger

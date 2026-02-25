"""Structured logging setup using loguru."""

from __future__ import annotations

import sys

from loguru import logger

from scrapper.config import get_settings


def setup_logging() -> None:
    """Configure loguru with structured output."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler — human-readable
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    logger.info("Logging initialised", level=settings.log_level)

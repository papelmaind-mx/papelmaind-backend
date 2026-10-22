"""Logging estructurado JSON — canon <stack> structlog JSON (F21: nunca console.log/print)."""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configura structlog JSON para producción y console para dev."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    terminator: list = [structlog.dev.ConsoleRenderer()]
    try:  # pragma: no cover
        structlog.processors.JSONRenderer()
    except Exception:  # pragma: no cover
        pass

    structlog.configure(
        processors=[*shared, structlog.processors.JSONRenderer()]
        if log_level.upper() == "INFO"
        else [*shared, *terminator],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("papelmind")

"""Structured logging configuration with optional Logfire integration."""

import logging
import sys


def setup_logging(log_level: str = "INFO", logfire_token: str = "") -> None:
    """Configure structured logging for the application.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        logfire_token: Optional Pydantic Logfire token for observability.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Logfire integration (optional)
    if logfire_token:
        try:
            import logfire as logfire_sdk

            logfire_sdk.configure(token=logfire_token)
            logfire_sdk.instrument_fastapi()
            logging.getLogger(__name__).info("Logfire integration enabled")
        except ImportError:
            logging.getLogger(__name__).warning(
                "Logfire token provided but logfire package not installed"
            )
        except Exception:
            logging.getLogger(__name__).exception("Failed to configure Logfire")

    logging.getLogger(__name__).info("Logging configured at %s level", log_level.upper())

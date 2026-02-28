# backend/app/core/logging_config.py
"""
Centralized Logging Configuration

Provides consistent logging across all modules with:
- Colored console output
- File logging (optional)
- Log levels configurable via environment
"""
import logging
import sys
import os
from typing import Optional


# Log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log level from environment (default: INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Add color based on log level
        color = self.COLORS.get(record.levelname, self.RESET)

        # Format the message
        formatted = super().format(record)

        # Apply color (only for console, not file)
        return f"{color}{formatted}{self.RESET}"


def setup_logging(
    name: str = "chainlens",
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for a module.

    Args:
        name: Logger name (usually module name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set level
    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger for a module.

    Usage:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)

        logger.info("Processing wallet %s", address)
        logger.error("Failed to fetch portfolio: %s", error)

    Args:
        name: Module name (usually __name__)

    Returns:
        Logger instance
    """
    return setup_logging(name)


# Pre-configured loggers for common modules
def get_adapter_logger() -> logging.Logger:
    """Logger for blockchain adapters."""
    return get_logger("chainlens.adapters")


def get_service_logger() -> logging.Logger:
    """Logger for services."""
    return get_logger("chainlens.services")


def get_router_logger() -> logging.Logger:
    """Logger for API routers."""
    return get_logger("chainlens.routers")


def get_db_logger() -> logging.Logger:
    """Logger for database operations."""
    return get_logger("chainlens.db")

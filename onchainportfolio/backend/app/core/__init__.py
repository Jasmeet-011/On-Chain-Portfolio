# backend/app/core/__init__.py
"""
Core module - Shared utilities and configuration.
"""
from .logging_config import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]

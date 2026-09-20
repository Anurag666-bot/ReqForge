"""
Logging setup for ReqForge.
"""

import logging
import sys
from typing import Optional
from ..config import get_config


def setup_logging() -> None:
    """Set up logging configuration."""
    config = get_config()
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(config.logging.format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if config.logging.file:
        file_handler = logging.FileHandler(config.logging.file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
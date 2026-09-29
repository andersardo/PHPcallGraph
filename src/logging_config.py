"""Logging configuration."""

import logging
import sys
from typing import Optional


def configure_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose (DEBUG) logging
        log_file: Optional file to log to
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s" if not verbose else format_str
    )
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(format_str)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)

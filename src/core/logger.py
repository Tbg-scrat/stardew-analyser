# src/core/logger.py

import os
import sys
import logging


class ColoredFormatter(logging.Formatter):
    """Custom logging formatter adding ANSI color codes for Docker terminal log readability."""

    COLOR_CODES = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        color = self.COLOR_CODES.get(record.levelno, self.RESET_CODE)
        original_levelname = record.levelname
        record.levelname = f"{color}[{record.levelname}]{self.RESET_CODE}"
        formatted_message = super().format(record)
        record.levelname = original_levelname
        return formatted_message


def setup_logging():
    """
    Configures application-wide logging.
    Sets log level to DEBUG if the 'DEBUG' environment variable is '1', 'true', or 'yes'.
    Defaults to INFO level otherwise.
    """
    debug_env = os.getenv("DEBUG", "").lower().strip()
    is_debug = debug_env in ("1", "true", "yes")

    log_level = logging.DEBUG if is_debug else logging.INFO

    formatter = ColoredFormatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    status_str = "ENABLED (DEBUG)" if is_debug else "DISABLED (INFO)"
    root_logger.info(f"Logging initialized. Debug mode: {status_str}")
    
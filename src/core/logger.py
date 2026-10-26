# src/core/logger.py

import glob
import logging
import os
import sys
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom logging formatter adding ANSI color codes for Docker terminal log readability."""

    COLOR_CODES = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
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


def prune_old_logs(log_dir: str, max_files: int = 20):
    """Keep only the N most recent log files in the log directory."""
    try:
        log_files = sorted(
            glob.glob(os.path.join(log_dir, "*.log")),
            key=os.path.getmtime,
            reverse=True,
        )
        for old_file in log_files[max_files:]:
            os.remove(old_file)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to clean up old log files in {log_dir}: {e}\n")


def is_module_debug_enabled(module_name: str) -> bool:
    """Checks if a given module (e.g., 'crops') is present in the DEBUG_MODULES allowlist environment variable."""
    raw_debug = os.getenv("DEBUG_MODULES", "")
    if not raw_debug:
        return False
    
    active_debugs = [m.strip().lower() for m in raw_debug.split(",")]
    return "*" in active_debugs or module_name.lower() in active_debugs


def setup_logging(process_name: str = "app"):
    """Configures application-wide logging.

    * Terminal (stdout): Uses colored output.
    * File (/log): Optional. Enabled automatically if '/log' directory exists.
    """
    debug_env = os.getenv("DEBUG", "").lower().strip()
    is_debug = debug_env in ("1", "true", "yes")

    log_level = logging.DEBUG if is_debug else logging.INFO

    # 1. Console Handler (Stdout with colors)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    handlers = [console_handler]

    # 2. File Handler (Optional via mount presence)
    log_dir = os.getenv("LOG_DIR", "/log")
    file_logging_path = None

    if os.path.isdir(log_dir):
        if os.access(log_dir, os.W_OK):
            try:
                prune_old_logs(log_dir, max_files=20)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_filename = f"{process_name}_{timestamp}.log"
                file_logging_path = os.path.join(log_dir, log_filename)

                # Plain-text formatter for file (no ANSI escape codes)
                file_formatter = logging.Formatter(
                    fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

                file_handler = logging.FileHandler(file_logging_path, encoding="utf-8")
                file_handler.setFormatter(file_formatter)
                handlers.append(file_handler)

            except Exception as e:
                sys.stderr.write(f"[WARN] Could not initialize file logging in {log_dir}: {e}\n")
        else:
            sys.stderr.write(f"[WARN] Log directory {log_dir} exists but is not writable.\n")

    # 3. Apply to Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    for h in handlers:
        root_logger.addHandler(h)

    # 4. Status Log
    status_str = "ENABLED (DEBUG)" if is_debug else "DISABLED (INFO)"
    root_logger.info(f"Logging initialized. Debug mode: {status_str}")

    if file_logging_path:
        root_logger.info(f"File logging active: {file_logging_path}")
        
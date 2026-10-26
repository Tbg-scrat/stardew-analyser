# tests/test_logger.py

import logging

from src.core.logger import prune_old_logs, setup_logging


def test_setup_logging_defaults_to_info(monkeypatch):
    """Ensures logging defaults to INFO level when DEBUG env var is not set."""
    monkeypatch.delenv("DEBUG", raising=False)
    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO


def test_setup_logging_enables_debug(monkeypatch):
    """Ensures setting DEBUG=1 configures root logger to DEBUG level."""
    monkeypatch.setenv("DEBUG", "1")
    setup_logging()

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_setup_logging_enables_debug_truthy_strings(monkeypatch):
    """Ensures 'true' or 'yes' also enable DEBUG level."""
    for truthy_val in ["true", "TRUE", "yes", "1"]:
        monkeypatch.setenv("DEBUG", truthy_val)
        setup_logging()
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG


def test_setup_logging_with_valid_log_dir(tmp_path, monkeypatch):
    """Verifies file logging is initialized if LOG_DIR exists and is writable."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    monkeypatch.setenv("LOG_DIR", str(log_dir))
    setup_logging("test_process")

    root_logger = logging.getLogger()
    # Check that a file handler was added
    has_file_handler = any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
    assert has_file_handler is True


def test_prune_old_logs(tmp_path):
    """Verifies old log files are successfully pruned past the max_files limit."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    # Create dummy log files
    for i in range(25):
        p = log_dir / f"log_{i}.log"
        p.write_text("data")

    prune_old_logs(str(log_dir), max_files=5)
    remaining_files = list(log_dir.glob("*.log"))
    assert len(remaining_files) == 5

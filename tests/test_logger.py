# tests/test_logger.py

import logging
from src.core.logger import setup_logging


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

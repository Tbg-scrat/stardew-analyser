# tests/test_logger.py

import logging

from src.core.logger import (
    ModuleDebugFilter,
    is_module_debug_enabled,
    setup_logging,
)


def test_module_debug_filter_default_info():
    filter_obj = ModuleDebugFilter()
    record = logging.LogRecord(
        name="src.modules.social",
        level=logging.DEBUG,
        pathname="/app/src/modules/social.py",
        lineno=10,
        msg="Debug test",
        args=(),
        exc_info=None,
    )
    # Debug records should be filtered out by default
    assert not filter_obj.filter(record)

    # Info records should always pass
    record.levelno = logging.INFO
    assert filter_obj.filter(record)


def test_module_debug_filter_specific_module(monkeypatch):
    monkeypatch.setenv("DEBUG_MODULES", "social")
    filter_obj = ModuleDebugFilter()

    # Leaf match "social" on "src.modules.social"
    record_debug = logging.LogRecord(
        name="src.modules.social",
        level=logging.DEBUG,
        pathname="/app/src/modules/social.py",
        lineno=10,
        msg="Debug social",
        args=(),
        exc_info=None,
    )
    assert filter_obj.filter(record_debug)

    # Unmatched module should be filtered out
    record_other = logging.LogRecord(
        name="src.modules.crops",
        level=logging.DEBUG,
        pathname="/app/src/modules/crops.py",
        lineno=10,
        msg="Debug crops",
        args=(),
        exc_info=None,
    )
    assert not filter_obj.filter(record_other)


def test_module_debug_filter_main_script_path_resolution(monkeypatch):
    monkeypatch.setenv("DEBUG_MODULES", "telemetry")
    filter_obj = ModuleDebugFilter()

    # Record executed as script (__name__ == "__main__")
    record_main = logging.LogRecord(
        name="__main__",
        level=logging.DEBUG,
        pathname="/app/src/core/telemetry.py",
        lineno=15,
        msg="Script execution debug",
        args=(),
        exc_info=None,
    )
    # Should inspect record.pathname and resolve "telemetry"
    assert filter_obj.filter(record_main)


def test_setup_logging_initialization():
    setup_logging("test-service")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) > 0


def test_is_module_debug_enabled_backwards_compatibility(monkeypatch):
    monkeypatch.setenv("DEBUG_MODULES", "fishing,shipping")
    assert is_module_debug_enabled("fishing")
    assert is_module_debug_enabled("shipping")
    assert not is_module_debug_enabled("crops")
    
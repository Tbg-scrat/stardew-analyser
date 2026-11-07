# src/core/logger.py

import logging
import os
import sys
from pathlib import Path

from opentelemetry._logs import get_logger_provider, set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


class ModuleDebugFilter(logging.Filter):
    """
    Filter that dynamically routes DEBUG log entries to console output based on
    DEBUG_MODULES and DOCKER_LOG_LEVEL environment variables.
    """

    def __init__(self, debug_modules_str=""):
        super().__init__()
        raw = os.getenv("DEBUG_MODULES", debug_modules_str)
        self.enabled_modules = {m.strip().lower() for m in raw.split(",") if m.strip()}
        self.global_debug = (
            os.getenv("DOCKER_LOG_LEVEL", "").upper() == "DEBUG"
            or "*" in self.enabled_modules
        )

    def filter(self, record):
        # 1. Always allow INFO, WARNING, ERROR, and CRITICAL logs
        if record.levelno > logging.DEBUG:
            return True

        # 2. Allow all DEBUG logs if global debug mode is enabled
        if self.global_debug:
            return True

        # 3. Resolve true module name (handles files executed directly as __main__)
        logger_name = record.name
        if logger_name == "__main__" and record.pathname:
            logger_name = Path(record.pathname).stem

        logger_name_lower = logger_name.lower()
        leaf_name = logger_name_lower.split(".")[-1]

        # 4. Match against DEBUG_MODULES (exact, leaf name, or package prefix)
        for target in self.enabled_modules:
            if (
                target == logger_name_lower
                or target == leaf_name
                or logger_name_lower.startswith(f"{target}.")
                or f".{target}." in logger_name_lower
            ):
                return True

        return False


def setup_logging(service_name="stardew-analyzer", **kwargs):
    """
    Initializes global logging with stdout formatting and OTLP gRPC export to Loki.
    Accepts **kwargs to gracefully handle legacy caller arguments.
    """
    docker_level_str = os.getenv("DOCKER_LOG_LEVEL", "INFO").upper()
    console_level = getattr(logging, docker_level_str, logging.INFO)

    # Force console base level to DEBUG if DEBUG_MODULES is set
    debug_modules = os.getenv("DEBUG_MODULES", "").strip()
    if debug_modules:
        console_level = logging.DEBUG

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs at root level
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Remove existing handlers to avoid duplicate log outputs across restarts
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # Dynamic filtering handled by ModuleDebugFilter
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ModuleDebugFilter())
    root_logger.addHandler(console_handler)

    # --- OTLP / Loki Handler ---
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"
    )
    otlp_active = False

    if otlp_endpoint:
        try:
            resource = Resource.create(
    {"service.name": os.getenv("OTEL_SERVICE_NAME", service_name)}
)

            # Prevent 'Overriding of current LoggerProvider' warning on re-initialization
            current_provider = get_logger_provider()
            if not isinstance(current_provider, LoggerProvider):
                logger_provider = LoggerProvider(resource=resource)
                set_logger_provider(logger_provider)
            else:
                logger_provider = current_provider

            # ZERO-ARGUMENT AUTO-CONFIG:
            # Let the OpenTelemetry SDK natively inspect environment variables
            # (OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_HEADERS, OTEL_EXPORTER_OTLP_INSECURE, etc.)
            exporter = OTLPLogExporter()
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

            otlp_handler = LoggingHandler(
                level=logging.DEBUG, logger_provider=logger_provider
            )
            # Prevent exporter feedback loop (urllib3 logs every export POST)
            otlp_handler.addFilter(
                lambda r: not r.name.startswith(("opentelemetry", "urllib3", "requests"))
            )
            root_logger.addHandler(otlp_handler)
            otlp_active = True
        except Exception as e:
            root_logger.warning(f"Failed to initialize OTLP log exporter: {e}")

    root_logger.info(
        f"Logging initialized. Console Level: {logging.getLevelName(console_level)}, "
        f"OTLP Logs: {'ACTIVE' if otlp_active else 'DISABLED'}"
    )


def is_module_debug_enabled(module_name: str) -> bool:
    """
    Legacy stub maintained for backwards compatibility.
    Deprecated: Use standard logger.debug() calls directly.
    """
    debug_modules = os.getenv("DEBUG_MODULES", "").strip()
    if not debug_modules:
        return False
    enabled = {m.strip().lower() for m in debug_modules.split(",") if m.strip()}
    return "*" in enabled or module_name.lower() in enabled
    
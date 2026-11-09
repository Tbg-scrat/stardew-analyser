import os

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def _setup_metrics():
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return
    resource = Resource.create(
        {"service.name": os.getenv("OTEL_SERVICE_NAME", "stardew-analyzer")}
    )
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(), export_interval_millis=30_000
    )
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[reader])
    )


_setup_metrics()  # runs once per process, on first import

meter = metrics.get_meter("stardew")
pipeline_duration = meter.create_histogram("stardew.pipeline.duration", unit="ms")
saves_parsed = meter.create_counter("stardew.saves.parsed")
achievements_unlocked = meter.create_gauge("stardew.achievements.unlocked")
"""OpenTelemetry setup — mirrors examples/minimal-service/telemetry.py in the kit.

Wires traces to Jaeger (OTLP) and metrics to Prometheus (a /metrics ASGI mount),
and auto-instruments FastAPI so every request produces http.server.* metrics and
a span. This is what makes the observability/ overlay show real data in Module
04. Set OTEL_ENABLED=false to skip entirely (tests do this).
"""

import logging

from fastapi import FastAPI

from .config import get_settings

logger = logging.getLogger("shopkit.telemetry")


def setup_telemetry(app: FastAPI) -> None:
    settings = get_settings()
    if not settings.otel_enabled:
        logger.info("OpenTelemetry disabled (OTEL_ENABLED=false)")
        return

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.semconv.resource import ResourceAttributes
        from prometheus_client import make_asgi_app
    except ImportError:  # pragma: no cover - OTel optional at runtime
        logger.warning("OpenTelemetry SDK not installed — skipping instrumentation")
        return

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: settings.otel_service_name,
            ResourceAttributes.SERVICE_VERSION: "0.1.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development",
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    prometheus_reader = PrometheusMetricReader()
    meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
    metrics.set_meter_provider(meter_provider)

    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, meter_provider=meter_provider
    )
    app.mount("/metrics", make_asgi_app())
    logger.info("OpenTelemetry tracing -> %s; /metrics mounted", settings.otlp_endpoint)

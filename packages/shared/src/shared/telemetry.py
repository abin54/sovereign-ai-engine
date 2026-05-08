import logging
import json
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

def setup_telemetry(service_name: str):
    resource = Resource.create({"service.name": service_name})
    
    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    # In production, use OTLP exporter. For now, console.
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
    
    # Metrics
    metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

class StructuredLogger:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
        # Standardize formatting to JSON
        handler = logging.StreamHandler()
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": self.formatTime(record),
                    "service": record.name,
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "trace_id": trace.get_current_span().get_span_context().trace_id if trace.get_current_span() else None,
                }
                if hasattr(record, "extra"):
                    log_data.update(record.extra)
                return json.dumps(log_data)
        
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def info(self, msg, **kwargs):
        self.logger.info(msg, extra=kwargs)

    def error(self, msg, **kwargs):
        self.logger.error(msg, extra=kwargs)

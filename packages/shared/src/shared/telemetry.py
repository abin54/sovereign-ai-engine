import logging
import json
import time
from functools import wraps
from typing import Any, Dict, Optional
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

# Tracing
tracer = trace.get_tracer("sovereign-ai")

def trace_llm_call(func):
    """Decorator to trace LLM calls with performance metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f"llm.{func.__name__}") as span:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                
                span.set_attribute("llm.duration_ms", duration_ms)
                span.set_attribute("llm.status", "success")
                
                return result
            except Exception as e:
                span.set_attribute("llm.status", "error")
                span.set_attribute("llm.error", str(e))
                raise
    
    return wrapper

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
        self.logger.info(msg, extra={"extra": kwargs})

    def warning(self, msg, **kwargs):
        self.logger.warning(msg, extra={"extra": kwargs})

    def error(self, msg, **kwargs):
        self.logger.error(msg, extra={"extra": kwargs})

    def debug(self, msg, **kwargs):
        self.logger.debug(msg, extra={"extra": kwargs})

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings
from app.core.db import engine


def configure_tracing(app: FastAPI) -> None:
    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "deployment.environment": settings.environment,
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{settings.otlp_endpoint}/v1/traces"))
    )
    trace.set_tracer_provider(provider)

    # Skip probe/scrape endpoints so they don't flood Jaeger with noise.
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine)

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel

from app.core.logging import get_logger
from app.core.metrics import provider_errors_total
from app.core.providers import CompletionResult, ProviderError
from app.core.registry import get_provider

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class ProviderTarget(BaseModel):
    provider: str
    model: str


class AllProvidersFailedError(Exception):
    def __init__(self, errors: list[ProviderError]) -> None:
        super().__init__("; ".join(str(e) for e in errors))
        self.errors = errors


async def complete_with_fallback(
    prompt: str, targets: list[ProviderTarget]
) -> tuple[CompletionResult, bool]:
    """
    Try each target in order. Returns (result, fallback_used).
    Raises AllProvidersFailedError if every target fails.
    """
    errors: list[ProviderError] = []

    for index, target in enumerate(targets):
        provider = get_provider(target.provider)

        with tracer.start_as_current_span("provider.complete") as span:
            span.set_attribute("llm.provider", target.provider)
            span.set_attribute("llm.model", target.model)
            span.set_attribute("llm.fallback_attempt", index)

            try:
                result = await provider.complete(prompt, target.model)
            except ProviderError as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                provider_errors_total.labels(provider=target.provider, model=target.model).inc()
                logger.warning(
                    "provider_failed",
                    provider=target.provider,
                    model=target.model,
                    error=str(e),
                    fallback_attempt=index,
                )
                errors.append(e)
                continue

            span.set_attribute("llm.input_tokens", result.input_tokens)
            span.set_attribute("llm.output_tokens", result.output_tokens)
            return result, index > 0

    raise AllProvidersFailedError(errors)

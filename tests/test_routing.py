import asyncio

import pytest
from prometheus_client import REGISTRY

from app.core.routing import AllProvidersFailedError, ProviderTarget, complete_with_fallback


def _provider_errors(provider: str, model: str) -> float:
    value = REGISTRY.get_sample_value(
        "provider_errors_total", {"provider": provider, "model": model}
    )
    return value or 0.0


def test_primary_success_does_not_use_fallback() -> None:
    targets = [
        ProviderTarget(provider="mock", model="primary-model"),
        ProviderTarget(provider="mock", model="backup-model"),
    ]

    result, fallback_used = asyncio.run(complete_with_fallback("hello", targets))

    assert result.model == "primary-model"
    assert fallback_used is False


def test_falls_back_when_primary_fails() -> None:
    errors_before = _provider_errors("mock-failing", "x")
    targets = [
        ProviderTarget(provider="mock-failing", model="x"),
        ProviderTarget(provider="mock", model="mock-model"),
    ]

    result, fallback_used = asyncio.run(complete_with_fallback("hello", targets))

    assert result.provider == "mock"
    assert fallback_used is True
    assert _provider_errors("mock-failing", "x") == errors_before + 1


def test_raises_when_every_provider_fails() -> None:
    targets = [
        ProviderTarget(provider="mock-failing", model="x"),
        ProviderTarget(provider="mock-failing", model="y"),
    ]

    with pytest.raises(AllProvidersFailedError) as exc_info:
        asyncio.run(complete_with_fallback("hello", targets))

    assert len(exc_info.value.errors) == 2

from app.core.config import settings
from app.core.providers import (
    AnthropicProvider,
    FailingMockProvider,
    MockProvider,
    OllamaProvider,
    Provider,
)


def _build_providers() -> dict[str, Provider]:
    providers: dict[str, Provider] = {
        "mock": MockProvider(),
        "mock-failing": FailingMockProvider(),
        "ollama": OllamaProvider(settings.ollama_base_url),
    }
    if settings.anthropic_api_key:
        providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    return providers


_providers = _build_providers()


def get_provider(name: str) -> Provider:
    if name not in _providers:
        raise ValueError(f"Unknown provider: {name}")
    return _providers[name]


def list_providers() -> list[str]:
    return list(_providers.keys())

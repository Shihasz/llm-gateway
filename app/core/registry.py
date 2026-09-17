from app.core.providers import MockProvider, Provider

_providers: dict[str, Provider] = {
    "mock": MockProvider(),
}


def get_provider(name: str) -> Provider:
    if name not in _providers:
        raise ValueError(f"Unknown provider: {name}")
    return _providers[name]


def list_providers() -> list[str]:
    return list(_providers.keys())

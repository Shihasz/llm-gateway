from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, cast

import httpx


class ProviderError(Exception):
    """Raised when a provider call fails (network error, timeout, non-2xx response)."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider


@dataclass
class CompletionResult:
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


class Provider(ABC):
    name: str

    @abstractmethod
    async def complete(self, prompt: str, model: str) -> CompletionResult:
        raise NotImplementedError


class MockProvider(Provider):
    """Deterministic stand-in provider so the gateway is runnable without API keys."""

    name = "mock"

    async def complete(self, prompt: str, model: str) -> CompletionResult:
        text = f"[mock response to: {prompt[:50]}]"
        return CompletionResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=len(prompt.split()),
            output_tokens=len(text.split()),
        )


class FailingMockProvider(Provider):
    """Always fails. Lets you exercise fallback routing without real outages."""

    name = "mock-failing"

    async def complete(self, prompt: str, model: str) -> CompletionResult:
        raise ProviderError(self.name, "simulated provider outage")


class AnthropicProvider(Provider):
    name = "anthropic"
    _url = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    async def complete(self, prompt: str, model: str) -> CompletionResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._url,
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(self.name, str(e)) from e

        data = cast("dict[str, Any]", response.json())
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = cast("dict[str, Any]", data.get("usage", {}))
        return CompletionResult(
            text=text,
            provider=self.name,
            model=model,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def complete(self, prompt: str, model: str) -> CompletionResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise ProviderError(self.name, str(e)) from e

        data = cast("dict[str, Any]", response.json())
        return CompletionResult(
            text=str(data.get("response", "")),
            provider=self.name,
            model=model,
            input_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
        )

from abc import ABC, abstractmethod
from dataclasses import dataclass


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

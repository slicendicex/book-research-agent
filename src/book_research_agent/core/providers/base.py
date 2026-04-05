from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str

    def embed_text(self, text: str) -> list[float]:
        ...


class GenerationProvider(Protocol):
    provider_name: str
    model_name: str

    def generate_text(self, prompt: str) -> str:
        ...


@dataclass(frozen=True)
class ProviderInfo:
    provider_name: str
    model_name: str

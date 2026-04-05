from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DummyEmbeddingProvider:
    provider_name: str
    model_name: str

    def embed_text(self, text: str) -> list[float]:
        size_hint = float(len(text.strip()))
        return [size_hint]


@dataclass(frozen=True)
class DummyGenerationProvider:
    provider_name: str
    model_name: str

    def generate_text(self, prompt: str) -> str:
        prompt_preview = prompt.strip()[:32]
        if not prompt_preview:
            prompt_preview = "empty-prompt"
        return f"dummy-response:{prompt_preview}"

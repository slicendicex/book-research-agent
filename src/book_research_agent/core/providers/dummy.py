from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DummyEmbeddingProvider:
    provider_name: str
    model_name: str

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        size_hint = float(len(text.strip()))
        type_hint = 1.0 if input_type == "search_query" else 0.0
        return [size_hint, type_hint]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


@dataclass(frozen=True)
class DummyGenerationProvider:
    provider_name: str
    model_name: str

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        prompt_preview = prompt.strip()[:32]
        if not prompt_preview:
            prompt_preview = "empty-prompt"
        return f"dummy-response:{prompt_preview}"

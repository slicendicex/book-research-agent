from __future__ import annotations

import os
from dataclasses import dataclass, field

import cohere


@dataclass
class CohereEmbeddingProvider:
    provider_name: str
    model_name: str
    _client: cohere.ClientV2 | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("COHERE_API_KEY", "").strip()
        if not api_key:
            raise ValueError("COHERE_API_KEY is required for the 'cohere' embedding provider")
        self._client = cohere.ClientV2(api_key=api_key)

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        return self.embed_texts([text], input_type=input_type)[0]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.embed(
            model=self.model_name,
            texts=texts,
            input_type=input_type,
            embedding_types=["float"],
        )
        return [list(vector) for vector in response.embeddings.float]

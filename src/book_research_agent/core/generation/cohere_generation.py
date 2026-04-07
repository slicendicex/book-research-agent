from __future__ import annotations

import os
from dataclasses import dataclass, field

import cohere


@dataclass
class CohereGenerationProvider:
    provider_name: str
    model_name: str
    _client: cohere.ClientV2 | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("COHERE_API_KEY", "").strip()
        if not api_key:
            raise ValueError("COHERE_API_KEY is required for the 'cohere' generation provider")
        self._client = cohere.ClientV2(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        response = self._client.chat(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=220,
            temperature=0.2,
        )
        return _extract_text_response(response)


def _extract_text_response(response: object) -> str:
    message = getattr(response, "message", None)
    content_items = getattr(message, "content", None) or []
    texts = []

    for item in content_items:
        if getattr(item, "type", None) != "text":
            continue
        text = getattr(item, "text", "").strip()
        if text:
            texts.append(text)

    if not texts:
        raise ValueError("Cohere generation response did not include text content")
    return "\n\n".join(texts)

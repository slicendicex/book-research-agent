from __future__ import annotations

import os
from dataclasses import dataclass, field

from openai import OpenAI

from .budgets import get_generation_output_budget


@dataclass
class OpenAIGenerationProvider:
    provider_name: str
    model_name: str
    _client: OpenAI | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the 'openai' generation provider")
        self._client = OpenAI(api_key=api_key)

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        response = self._client.responses.create(
            model=self.model_name,
            input=prompt,
            max_output_tokens=output_budget or get_generation_output_budget("answer"),
            temperature=0.2,
        )
        return _extract_text_response(response)


def _extract_text_response(response: object) -> str:
    output_text = getattr(response, "output_text", "")
    if output_text.strip():
        return output_text.strip()

    texts: list[str] = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            text = getattr(content_item, "text", "").strip()
            if text:
                texts.append(text)

    if not texts:
        raise ValueError("OpenAI generation response did not include text content")
    return "\n\n".join(texts)

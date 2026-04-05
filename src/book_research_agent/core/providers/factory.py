from __future__ import annotations

from book_research_agent.core.config.settings import RuntimeSettings
from book_research_agent.core.providers.base import (
    EmbeddingProvider,
    GenerationProvider,
)
from book_research_agent.core.providers.dummy import (
    DummyEmbeddingProvider,
    DummyGenerationProvider,
)


def _not_implemented_provider(provider_name: str, provider_kind: str) -> NotImplementedError:
    return NotImplementedError(
        f"{provider_kind} provider '{provider_name}' is not implemented yet. "
        "Use 'dummy' for local scaffold verification."
    )


def create_embedding_provider(settings: RuntimeSettings) -> EmbeddingProvider:
    provider_name = settings.embedding_provider.lower()

    if provider_name == "dummy":
        return DummyEmbeddingProvider(
            provider_name=provider_name,
            model_name=settings.embedding_model,
        )

    if provider_name in {"openai", "gemini", "anthropic"}:
        raise _not_implemented_provider(provider_name, "embedding")

    raise NotImplementedError(
        f"Unsupported embedding provider '{settings.embedding_provider}'."
    )


def create_generation_provider(settings: RuntimeSettings) -> GenerationProvider:
    provider_name = settings.generation_provider.lower()

    if provider_name == "dummy":
        return DummyGenerationProvider(
            provider_name=provider_name,
            model_name=settings.generation_model,
        )

    if provider_name in {"openai", "gemini", "anthropic"}:
        raise _not_implemented_provider(provider_name, "generation")

    raise NotImplementedError(
        f"Unsupported generation provider '{settings.generation_provider}'."
    )

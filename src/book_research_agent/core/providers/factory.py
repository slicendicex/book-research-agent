from __future__ import annotations

from book_research_agent.core.config.settings import RuntimeSettings
from book_research_agent.core.generation import (
    CohereGenerationProvider,
    OpenAIGenerationProvider,
)
from book_research_agent.core.providers.base import (
    EmbeddingProvider,
    GenerationProvider,
)
from book_research_agent.core.providers.cohere_embeddings import CohereEmbeddingProvider
from book_research_agent.core.providers.dummy import (
    DummyEmbeddingProvider,
    DummyGenerationProvider,
)
from book_research_agent.core.providers.openai_embeddings import OpenAIEmbeddingProvider

DEFAULT_COHERE_GENERATION_MODEL = "command-a-03-2025"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_OPENAI_GENERATION_MODEL = "gpt-4.1-mini"


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

    if provider_name == "cohere":
        return CohereEmbeddingProvider(
            provider_name=provider_name,
            model_name=settings.embedding_model,
        )

    if provider_name == "openai":
        return OpenAIEmbeddingProvider(
            provider_name=provider_name,
            model_name=_resolve_openai_embedding_model(settings),
        )

    if provider_name in {"gemini", "anthropic"}:
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

    if provider_name == "cohere":
        return CohereGenerationProvider(
            provider_name=provider_name,
            model_name=_resolve_cohere_generation_model(settings),
        )

    if provider_name == "openai":
        return OpenAIGenerationProvider(
            provider_name=provider_name,
            model_name=_resolve_openai_generation_model(settings),
        )

    if provider_name in {"gemini", "anthropic"}:
        raise _not_implemented_provider(provider_name, "generation")

    raise NotImplementedError(
        f"Unsupported generation provider '{settings.generation_provider}'."
    )


def _resolve_cohere_generation_model(settings: RuntimeSettings) -> str:
    if settings.generation_model == "dummy-generation-v1":
        return DEFAULT_COHERE_GENERATION_MODEL
    return settings.generation_model


def _resolve_openai_embedding_model(settings: RuntimeSettings) -> str:
    if settings.embedding_model == "embed-v4.0":
        return DEFAULT_OPENAI_EMBEDDING_MODEL
    return settings.embedding_model


def _resolve_openai_generation_model(settings: RuntimeSettings) -> str:
    if settings.generation_model in {"dummy-generation-v1", DEFAULT_COHERE_GENERATION_MODEL}:
        return DEFAULT_OPENAI_GENERATION_MODEL
    return settings.generation_model

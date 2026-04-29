from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from book_research_agent.core.config.settings import RuntimeSettings
from book_research_agent.core.generation.cohere_generation import CohereGenerationProvider
from book_research_agent.core.generation.openai_generation import OpenAIGenerationProvider
from book_research_agent.core.providers.factory import create_generation_provider


class GenerationProviderTests(unittest.TestCase):
    def test_cohere_generation_provider_raises_when_api_key_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "COHERE_API_KEY is required",
            ):
                CohereGenerationProvider(
                    provider_name="cohere",
                    model_name="command-a-03-2025",
                )

    def test_cohere_generation_provider_returns_text_content(self) -> None:
        response = SimpleNamespace(
            message=SimpleNamespace(
                content=[
                    SimpleNamespace(type="text", text="Grounded answer."),
                ]
            )
        )

        with patch.dict(os.environ, {"COHERE_API_KEY": "test-key"}, clear=True):
            with patch(
                "book_research_agent.core.generation.cohere_generation.cohere.ClientV2"
            ) as client_cls:
                client_cls.return_value.chat.return_value = response
                provider = CohereGenerationProvider(
                    provider_name="cohere",
                    model_name="command-a-03-2025",
                )

        self.assertEqual(
            provider.generate_text("prompt text", output_budget=1400),
            "Grounded answer.",
        )
        client_cls.return_value.chat.assert_called_once()
        self.assertEqual(
            client_cls.return_value.chat.call_args.kwargs["max_tokens"],
            1400,
        )

    def test_openai_generation_provider_raises_when_api_key_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "OPENAI_API_KEY is required",
            ):
                OpenAIGenerationProvider(
                    provider_name="openai",
                    model_name="gpt-4.1-mini",
                )

    def test_openai_generation_provider_returns_output_text(self) -> None:
        response = SimpleNamespace(output_text="Grounded OpenAI answer.")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch(
                "book_research_agent.core.generation.openai_generation.OpenAI"
            ) as client_cls:
                client_cls.return_value.responses.create.return_value = response
                provider = OpenAIGenerationProvider(
                    provider_name="openai",
                    model_name="gpt-4.1-mini",
                )

        self.assertEqual(
            provider.generate_text("prompt text", output_budget=900),
            "Grounded OpenAI answer.",
        )
        client_cls.return_value.responses.create.assert_called_once()
        self.assertEqual(
            client_cls.return_value.responses.create.call_args.kwargs["max_output_tokens"],
            900,
        )

    def test_provider_factory_returns_openai_generation_provider(self) -> None:
        settings = RuntimeSettings(
            environment="test",
            embedding_provider="dummy",
            embedding_model="dummy-embedding-v1",
            generation_provider="openai",
            generation_model="gpt-4.1-mini",
            has_cohere_api_key=False,
            has_openai_api_key=True,
            has_gemini_api_key=False,
            has_anthropic_api_key=False,
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            provider = create_generation_provider(settings)

        self.assertIsInstance(provider, OpenAIGenerationProvider)
        self.assertEqual(provider.model_name, "gpt-4.1-mini")


if __name__ == "__main__":
    unittest.main()

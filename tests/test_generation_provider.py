from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from book_research_agent.core.generation.cohere_generation import CohereGenerationProvider


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

        self.assertEqual(provider.generate_text("prompt text"), "Grounded answer.")


if __name__ == "__main__":
    unittest.main()

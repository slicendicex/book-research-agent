from __future__ import annotations

import argparse
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from book_research_agent.cli import run_doctor
from book_research_agent.core.config import env
from book_research_agent.core.config.env import get_env_var_status, load_project_env


class EnvSourceTrackingTests(unittest.TestCase):
    def setUp(self) -> None:
        env._ENV_SOURCES.clear()

    def test_load_project_env_reports_env_fallback_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("COHERE_API_KEY=from-file\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                load_project_env(env_path)
                status = get_env_var_status("COHERE_API_KEY")

        self.assertTrue(status.present)
        self.assertEqual(status.source, ".env")

    def test_shell_env_takes_precedence_over_env_file_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("COHERE_API_KEY=from-file\n", encoding="utf-8")

            with patch.dict(os.environ, {"COHERE_API_KEY": "from-shell"}, clear=True):
                load_project_env(env_path)
                status = get_env_var_status("COHERE_API_KEY")
                value = os.environ["COHERE_API_KEY"]

        self.assertTrue(status.present)
        self.assertEqual(status.source, "shell_env")
        self.assertEqual(value, "from-shell")

    def test_missing_env_var_reports_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            status = get_env_var_status("ANTHROPIC_API_KEY")

        self.assertFalse(status.present)
        self.assertEqual(status.source, "missing")

    def test_doctor_prints_sources_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "COHERE_API_KEY=cohere-secret",
                        "ANTHROPIC_API_KEY=anthropic-secret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "openai-secret",
                    "BOOK_RESEARCH_AGENT_EMBEDDING_PROVIDER": "dummy",
                    "BOOK_RESEARCH_AGENT_GENERATION_PROVIDER": "dummy",
                },
                clear=True,
            ):
                load_project_env(env_path)
                output = io.StringIO()
                with redirect_stdout(output):
                    run_doctor(argparse.Namespace())

        text = output.getvalue()
        self.assertIn("cohere_api_key_present: yes", text)
        self.assertIn("cohere_api_key_source: .env", text)
        self.assertIn("openai_api_key_present: yes", text)
        self.assertIn("openai_api_key_source: shell_env", text)
        self.assertIn("anthropic_api_key_present: yes", text)
        self.assertIn("anthropic_api_key_source: .env", text)
        self.assertNotIn("cohere-secret", text)
        self.assertNotIn("openai-secret", text)
        self.assertNotIn("anthropic-secret", text)


if __name__ == "__main__":
    unittest.main()

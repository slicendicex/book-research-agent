from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"


def _read_env(name: str, default: str) -> str:
    value = os.environ.get(name, default).strip()
    return value or default


def _has_env_value(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    embedding_provider: str
    embedding_model: str
    generation_provider: str
    generation_model: str
    has_openai_api_key: bool
    has_gemini_api_key: bool
    has_anthropic_api_key: bool
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    docs_dir: Path = DOCS_DIR

    @property
    def data_raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def data_processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def data_index_dir(self) -> Path:
        return self.data_dir / "index"


def load_settings() -> RuntimeSettings:
    return RuntimeSettings(
        environment=_read_env("BOOK_RESEARCH_AGENT_ENV", "local"),
        embedding_provider=_read_env(
            "BOOK_RESEARCH_AGENT_EMBEDDING_PROVIDER",
            "dummy",
        ),
        embedding_model=_read_env(
            "BOOK_RESEARCH_AGENT_EMBEDDING_MODEL",
            "dummy-embedding-v1",
        ),
        generation_provider=_read_env(
            "BOOK_RESEARCH_AGENT_GENERATION_PROVIDER",
            "dummy",
        ),
        generation_model=_read_env(
            "BOOK_RESEARCH_AGENT_GENERATION_MODEL",
            "dummy-generation-v1",
        ),
        has_openai_api_key=_has_env_value("OPENAI_API_KEY"),
        has_gemini_api_key=_has_env_value("GEMINI_API_KEY"),
        has_anthropic_api_key=_has_env_value("ANTHROPIC_API_KEY"),
    )

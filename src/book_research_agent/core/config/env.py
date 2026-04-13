from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from book_research_agent.core.config.settings import PROJECT_ROOT


@dataclass(frozen=True)
class EnvVarStatus:
    present: bool
    source: str


_ENV_SOURCES: dict[str, str] = {}


def load_project_env(env_path: Path | None = None) -> None:
    path = env_path or (PROJECT_ROOT / ".env")
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        if not key:
            continue

        cleaned_value = _clean_env_value(value.strip())

        if key in os.environ:
            if _ENV_SOURCES.get(key) == ".env" and os.environ[key] == cleaned_value:
                continue
            _ENV_SOURCES[key] = "shell_env"
            continue

        os.environ[key] = cleaned_value
        _ENV_SOURCES[key] = ".env"


def get_env_var_status(name: str) -> EnvVarStatus:
    present = bool(os.environ.get(name, "").strip())
    if not present:
        return EnvVarStatus(present=False, source="missing")
    return EnvVarStatus(present=True, source=_ENV_SOURCES.get(name, "shell_env"))


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value

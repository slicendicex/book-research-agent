from __future__ import annotations

import os
from pathlib import Path

from book_research_agent.core.config.settings import PROJECT_ROOT


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
        if not key or key in os.environ:
            continue

        os.environ[key] = _clean_env_value(value.strip())


def _clean_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value

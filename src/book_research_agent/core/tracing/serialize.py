from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from .models import RagTraceArtifact


def build_default_trace_path(
    traces_dir: Path,
    *,
    mode: str,
    now: datetime | None = None,
) -> Path:
    timestamp = now or datetime.now()
    normalized_mode = mode.replace(" ", "-").replace("/", "-")
    for offset in range(0, 60):
        candidate_time = timestamp + timedelta(seconds=offset)
        candidate = (
            traces_dir
            / f"{candidate_time.strftime('%Y-%m-%dT%H-%M-%S')}_{normalized_mode}_trace.json"
        )
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not allocate a unique trace artifact path")


def write_trace_json(path: Path, *, trace: RagTraceArtifact) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

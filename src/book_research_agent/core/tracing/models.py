from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class TraceEvidenceBlock:
    chunk_id: str
    title: str
    relative_path: str
    chunk_index: int
    score: float
    evidence_block: str


@dataclass(frozen=True)
class TraceSide:
    query: str
    retrieval_candidates: list[TraceEvidenceBlock] = field(default_factory=list)
    final_evidence: list[TraceEvidenceBlock] = field(default_factory=list)


@dataclass(frozen=True)
class RagTraceArtifact:
    mode: str
    generated_output: str
    query: str | None = None
    retrieval_candidates: list[TraceEvidenceBlock] = field(default_factory=list)
    final_evidence: list[TraceEvidenceBlock] = field(default_factory=list)
    left: TraceSide | None = None
    right: TraceSide | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

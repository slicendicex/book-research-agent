from __future__ import annotations

from dataclasses import dataclass

from .search import SearchResult


@dataclass(frozen=True)
class SourceResult:
    score: float
    title: str
    relative_path: str
    chunk_index: int
    excerpt: str


def format_excerpt(
    text: str,
    *,
    max_length: int = 160,
    trim_start_word: bool = False,
) -> str:
    if max_length <= 0:
        raise ValueError("max_length must be greater than zero")

    normalized = " ".join(text.split())
    if not normalized:
        return ""

    start_trimmed = False
    if trim_start_word and " " in normalized:
        normalized = normalized.split(" ", maxsplit=1)[1].lstrip()
        start_trimmed = True

    if len(normalized) <= max_length:
        return _add_prefix(normalized, start_trimmed)

    boundary_candidate = normalized[:max_length].rstrip()
    boundary = boundary_candidate.rfind(" ")
    if boundary >= max_length // 2:
        truncated = boundary_candidate[:boundary].rstrip()
    else:
        truncated = normalized[: max_length - 3].rstrip()

    return f"{_add_prefix(truncated, start_trimmed)}..."


def filter_neighboring_results(
    search_results: list[SearchResult],
    *,
    neighbor_window: int = 1,
) -> list[SearchResult]:
    if neighbor_window < 0:
        raise ValueError("neighbor_window must be zero or greater")

    kept_results: list[SearchResult] = []

    for result in search_results:
        if _is_close_neighbor(result, kept_results, neighbor_window=neighbor_window):
            continue
        kept_results.append(result)

    return kept_results


def build_source_results(
    search_results: list[SearchResult],
    *,
    max_results: int | None = None,
    excerpt_length: int = 160,
    neighbor_window: int = 1,
) -> list[SourceResult]:
    filtered_results = filter_neighboring_results(
        search_results,
        neighbor_window=neighbor_window,
    )
    if max_results is not None:
        filtered_results = filtered_results[:max_results]

    return [
        SourceResult(
            score=result.score,
            title=result.indexed_chunk.metadata.source_title,
            relative_path=result.indexed_chunk.metadata.document_relative_path,
            chunk_index=result.indexed_chunk.metadata.chunk_index,
            excerpt=format_excerpt(
                result.indexed_chunk.text,
                max_length=excerpt_length,
                trim_start_word=result.indexed_chunk.metadata.char_start > 0,
            ),
        )
        for result in filtered_results
    ]


def _add_prefix(text: str, start_trimmed: bool) -> str:
    if not start_trimmed:
        return text
    return f"... {text}"


def _is_close_neighbor(
    candidate: SearchResult,
    kept_results: list[SearchResult],
    *,
    neighbor_window: int,
) -> bool:
    candidate_chunk = candidate.indexed_chunk

    for kept in kept_results:
        kept_chunk = kept.indexed_chunk
        if kept_chunk.document_id != candidate_chunk.document_id:
            continue
        if (
            abs(
                kept_chunk.metadata.chunk_index
                - candidate_chunk.metadata.chunk_index
            )
            <= neighbor_window
        ):
            return True

    return False

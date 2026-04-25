from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from book_research_agent.core.answering import (
    answer_query,
    canon_query,
    compare_queries,
    contradict_queries,
)
from book_research_agent.core.evaluation.models import (
    EvalCase,
    EvalResult,
    EvalRetrievalSnapshot,
    EvalSummary,
)
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.core.retrieval import (
    filter_neighboring_results,
    rerank_search_results,
    search_index,
)


ANSWER_MODES = {"answer", "canon", "compare", "contradict"}


def read_eval_cases_jsonl(path: Path) -> list[EvalCase]:
    if not path.exists():
        raise FileNotFoundError(f"Eval cases file not found: {path}")

    cases: list[EvalCase] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        try:
            case = EvalCase(
                id=str(payload["id"]).strip(),
                mode=str(payload["mode"]).strip(),
                query=str(payload["query"]).strip(),
                notes=str(payload.get("notes", "")).strip(),
            )
        except KeyError as error:
            raise ValueError(f"Missing eval case field on line {line_number}: {error}") from error
        if not case.id or not case.mode or not case.query:
            raise ValueError(f"Invalid empty eval case field on line {line_number}")
        cases.append(case)
    return cases


def run_eval_cases(
    cases: list[EvalCase],
    *,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = 3,
    warn_below: int = 2,
) -> list[EvalResult]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    if warn_below <= 0:
        raise ValueError("warn_below must be greater than zero")

    return [
        _run_eval_case(
            case,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
            warn_below=warn_below,
        )
        for case in cases
    ]


def summarize_eval_results(results: list[EvalResult]) -> EvalSummary:
    return EvalSummary(
        pass_count=sum(1 for result in results if result.status == "PASS"),
        warn_count=sum(1 for result in results if result.status == "WARN"),
        fail_count=sum(1 for result in results if result.status == "FAIL"),
    )


def write_eval_report_json(
    path: Path,
    *,
    results: list[EvalResult],
    summary: EvalSummary,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": asdict(summary),
        "results": [asdict(result) for result in results],
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _run_eval_case(
    case: EvalCase,
    *,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
    warn_below: int,
) -> EvalResult:
    try:
        retrieval_snapshots = _retrieval_snapshots(
            case,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        )
    except ValueError as error:
        return EvalResult(
            case_id=case.id,
            mode=case.mode,
            status="FAIL",
            retrieval_count=0,
            answer_present=False,
            message=str(error),
            retrieval_snapshots=[],
        )

    retrieval_count = min(
        (len(snapshot.top_chunk_ids) for snapshot in retrieval_snapshots),
        default=0,
    )

    if retrieval_count == 0:
        return EvalResult(
            case_id=case.id,
            mode=case.mode,
            status="FAIL",
            retrieval_count=0,
            answer_present=False,
            message="no retrieval",
            retrieval_snapshots=retrieval_snapshots,
        )

    answer_text = _run_answer_mode(
        case,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    answer_present = bool(answer_text.strip())
    if not answer_present:
        return EvalResult(
            case_id=case.id,
            mode=case.mode,
            status="FAIL",
            retrieval_count=retrieval_count,
            answer_present=False,
            message="empty answer",
            retrieval_snapshots=retrieval_snapshots,
        )

    if retrieval_count < warn_below:
        return EvalResult(
            case_id=case.id,
            mode=case.mode,
            status="WARN",
            retrieval_count=retrieval_count,
            answer_present=True,
            message="low retrieval",
            retrieval_snapshots=retrieval_snapshots,
        )

    return EvalResult(
        case_id=case.id,
        mode=case.mode,
        status="PASS",
        retrieval_count=retrieval_count,
        answer_present=True,
        retrieval_snapshots=retrieval_snapshots,
    )


def _retrieval_snapshots(
    case: EvalCase,
    *,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
) -> list[EvalRetrievalSnapshot]:
    queries = _case_queries(case)
    return [
        _run_retrieval_snapshot(
            query=query,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        )
        for query in queries
    ]


def _run_retrieval_snapshot(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
) -> EvalRetrievalSnapshot:
    candidate_results = search_index(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=max(top_k * 3, top_k),
    )
    filtered_results = filter_neighboring_results(candidate_results)
    final_results = rerank_search_results(
        query=query,
        candidates=filtered_results,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    top_paths = [
        result.indexed_chunk.metadata.document_relative_path for result in final_results
    ]
    top_titles = [result.indexed_chunk.metadata.source_title for result in final_results]
    top_chunk_ids = [result.indexed_chunk.chunk_id for result in final_results]
    top_scores = [round(result.score, 4) for result in final_results]
    unique_document_count = len(
        {result.indexed_chunk.document_id for result in final_results}
    )
    path_counts: dict[str, int] = {}
    for path in top_paths:
        path_counts[path] = path_counts.get(path, 0) + 1

    return EvalRetrievalSnapshot(
        query=query,
        top_paths=top_paths,
        top_titles=top_titles,
        top_chunk_ids=top_chunk_ids,
        top_scores=top_scores,
        unique_document_count=unique_document_count,
        top_path_repeat_count=max(path_counts.values(), default=0),
        duplicate_like_count=max(len(candidate_results) - len(filtered_results), 0),
        score_spread=(
            round(max(top_scores) - min(top_scores), 4)
            if len(top_scores) >= 2
            else 0.0
        ),
    )


def _run_answer_mode(
    case: EvalCase,
    *,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
) -> str:
    if case.mode == "answer":
        return answer_query(
            query=case.query,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        ).answer
    if case.mode == "canon":
        return canon_query(
            query=case.query,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        ).judgment
    if case.mode == "compare":
        left_query, right_query = _split_pair_query(case.query)
        return compare_queries(
            left_query=left_query,
            right_query=right_query,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        ).comparison
    if case.mode == "contradict":
        left_query, right_query = _split_pair_query(case.query)
        return contradict_queries(
            left_query=left_query,
            right_query=right_query,
            indexed_chunks=indexed_chunks,
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
            top_k=top_k,
        ).judgment
    raise ValueError(f"Unsupported eval mode: {case.mode}")


def _case_queries(case: EvalCase) -> list[str]:
    if case.mode in {"compare", "contradict"}:
        return list(_split_pair_query(case.query))
    if case.mode in {"answer", "canon"}:
        return [case.query]
    raise ValueError(f"Unsupported eval mode: {case.mode}")


def _split_pair_query(query: str) -> tuple[str, str]:
    parts = [part.strip() for part in query.split("||", maxsplit=1)]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("Pair eval query must use 'left || right'")
    return parts[0], parts[1]

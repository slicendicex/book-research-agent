from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from book_research_agent.core.answering import (
    answer_query,
    canon_query,
    compare_queries,
    contradict_queries,
)
from book_research_agent.core.evaluation.models import (
    EvalCase,
    EvalCaseDiff,
    EvalRunDiff,
    EvalRunReport,
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
AUTO_SAVED_RUN_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}_eval\.json$")
DEFAULT_EVAL_RUN_HISTORY_LIMIT = 20


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


def read_eval_report_json(path: Path) -> EvalRunReport:
    if not path.exists():
        raise FileNotFoundError(f"Eval report file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    summary_payload = payload.get("summary")
    results_payload = payload.get("results")
    if not isinstance(summary_payload, dict) or not isinstance(results_payload, list):
        raise ValueError(f"Invalid eval report format: {path}")

    return EvalRunReport(
        summary=EvalSummary(
            pass_count=int(summary_payload["pass_count"]),
            warn_count=int(summary_payload["warn_count"]),
            fail_count=int(summary_payload["fail_count"]),
        ),
        results=[_deserialize_eval_result(item) for item in results_payload],
    )


def build_default_eval_run_path(
    runs_dir: Path,
    *,
    now: datetime | None = None,
) -> Path:
    timestamp = now or datetime.now()
    for offset in range(0, 60):
        candidate_time = timestamp + timedelta(seconds=offset)
        candidate = runs_dir / f"{candidate_time.strftime('%Y-%m-%dT%H-%M-%S')}_eval.json"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not allocate a unique auto-saved eval run path")


def prune_auto_saved_eval_runs(
    runs_dir: Path,
    *,
    keep_last: int = DEFAULT_EVAL_RUN_HISTORY_LIMIT,
) -> list[Path]:
    if keep_last <= 0:
        raise ValueError("keep_last must be greater than zero")
    if not runs_dir.exists():
        return []

    auto_saved_paths = sorted(
        (
            path
            for path in runs_dir.iterdir()
            if path.is_file() and AUTO_SAVED_RUN_PATTERN.match(path.name)
        ),
        key=lambda path: path.name,
    )
    if len(auto_saved_paths) <= keep_last:
        return []

    removed_paths: list[Path] = []
    for path in auto_saved_paths[:-keep_last]:
        path.unlink()
        removed_paths.append(path)
    return removed_paths


def resolve_eval_run_path(path_text: str, *, runs_dir: Path) -> Path:
    candidate = Path(path_text)
    if candidate.exists():
        return candidate

    short_candidate = runs_dir / path_text
    if short_candidate.exists():
        return short_candidate

    raise FileNotFoundError(f"Eval run file not found: {path_text}")


def get_latest_eval_run_paths(runs_dir: Path) -> tuple[Path, Path]:
    if not runs_dir.exists():
        raise FileNotFoundError(f"Eval runs directory not found: {runs_dir}")

    report_paths: list[Path] = []
    for path in sorted(
        runs_dir.iterdir(),
        key=lambda item: (item.stat().st_mtime, item.name),
        reverse=True,
    ):
        if not path.is_file() or path.suffix != ".json":
            continue
        try:
            read_eval_report_json(path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError, KeyError, TypeError):
            continue
        report_paths.append(path)
        if len(report_paths) == 2:
            return report_paths[1], report_paths[0]

    raise ValueError("At least two eval run files are required for --latest")


def build_eval_run_diff(
    before_report: EvalRunReport,
    after_report: EvalRunReport,
    *,
    before_path: Path,
    after_path: Path,
) -> EvalRunDiff:
    before_by_case = {result.case_id: result for result in before_report.results}
    after_by_case = {result.case_id: result for result in after_report.results}

    changed_cases: list[EvalCaseDiff] = []
    for case_id in sorted(set(before_by_case) | set(after_by_case)):
        before_result = before_by_case.get(case_id)
        after_result = after_by_case.get(case_id)
        case_diff = _build_case_diff(case_id, before_result, after_result)
        if case_diff is not None:
            changed_cases.append(case_diff)

    return EvalRunDiff(
        before_path=before_path,
        after_path=after_path,
        pass_delta=after_report.summary.pass_count - before_report.summary.pass_count,
        warn_delta=after_report.summary.warn_count - before_report.summary.warn_count,
        fail_delta=after_report.summary.fail_count - before_report.summary.fail_count,
        changed_cases=changed_cases,
    )


def write_eval_diff_json(path: Path, *, diff: EvalRunDiff) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "before_path": str(diff.before_path),
        "after_path": str(diff.after_path),
        "summary_delta": {
            "pass_delta": diff.pass_delta,
            "warn_delta": diff.warn_delta,
            "fail_delta": diff.fail_delta,
        },
        "changed_cases": [asdict(case_diff) for case_diff in diff.changed_cases],
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


def _deserialize_eval_result(payload: object) -> EvalResult:
    if not isinstance(payload, dict):
        raise ValueError("Invalid eval result payload")

    snapshots_payload = payload.get("retrieval_snapshots", [])
    if not isinstance(snapshots_payload, list):
        raise ValueError("Invalid retrieval_snapshots payload")

    return EvalResult(
        case_id=str(payload["case_id"]),
        mode=str(payload["mode"]),
        status=str(payload["status"]),
        retrieval_count=int(payload["retrieval_count"]),
        answer_present=bool(payload["answer_present"]),
        message=str(payload.get("message", "")),
        retrieval_snapshots=[
            _deserialize_snapshot(snapshot_payload)
            for snapshot_payload in snapshots_payload
        ],
    )


def _deserialize_snapshot(payload: object) -> EvalRetrievalSnapshot:
    if not isinstance(payload, dict):
        raise ValueError("Invalid eval retrieval snapshot payload")

    return EvalRetrievalSnapshot(
        query=str(payload["query"]),
        top_paths=[str(item) for item in payload.get("top_paths", [])],
        top_titles=[str(item) for item in payload.get("top_titles", [])],
        top_chunk_ids=[str(item) for item in payload.get("top_chunk_ids", [])],
        top_scores=[float(item) for item in payload.get("top_scores", [])],
        unique_document_count=int(payload.get("unique_document_count", 0)),
        top_path_repeat_count=int(payload.get("top_path_repeat_count", 0)),
        duplicate_like_count=int(payload.get("duplicate_like_count", 0)),
        score_spread=float(payload.get("score_spread", 0.0)),
    )


def _build_case_diff(
    case_id: str,
    before_result: EvalResult | None,
    after_result: EvalResult | None,
) -> EvalCaseDiff | None:
    status_before = before_result.status if before_result is not None else None
    status_after = after_result.status if after_result is not None else None
    retrieval_count_before = (
        before_result.retrieval_count if before_result is not None else None
    )
    retrieval_count_after = after_result.retrieval_count if after_result is not None else None
    top_paths_before = _collect_snapshot_lists(before_result, field_name="top_paths")
    top_paths_after = _collect_snapshot_lists(after_result, field_name="top_paths")
    top_scores_before = _collect_snapshot_lists(before_result, field_name="top_scores")
    top_scores_after = _collect_snapshot_lists(after_result, field_name="top_scores")
    unique_before = _collect_snapshot_scalars(
        before_result,
        field_name="unique_document_count",
    )
    unique_after = _collect_snapshot_scalars(
        after_result,
        field_name="unique_document_count",
    )
    duplicate_before = _collect_snapshot_scalars(
        before_result,
        field_name="duplicate_like_count",
    )
    duplicate_after = _collect_snapshot_scalars(
        after_result,
        field_name="duplicate_like_count",
    )

    if (
        status_before == status_after
        and retrieval_count_before == retrieval_count_after
        and top_paths_before == top_paths_after
        and top_scores_before == top_scores_after
        and unique_before == unique_after
        and duplicate_before == duplicate_after
    ):
        return None

    mode = (
        before_result.mode
        if before_result is not None
        else after_result.mode
        if after_result is not None
        else "unknown"
    )
    return EvalCaseDiff(
        case_id=case_id,
        mode=mode,
        status_before=status_before,
        status_after=status_after,
        retrieval_count_before=retrieval_count_before,
        retrieval_count_after=retrieval_count_after,
        top_paths_before=top_paths_before,
        top_paths_after=top_paths_after,
        top_scores_before=top_scores_before,
        top_scores_after=top_scores_after,
        unique_document_count_before=unique_before,
        unique_document_count_after=unique_after,
        duplicate_like_count_before=duplicate_before,
        duplicate_like_count_after=duplicate_after,
    )


def _collect_snapshot_lists(
    result: EvalResult | None,
    *,
    field_name: str,
) -> list[list[str]] | list[list[float]]:
    if result is None:
        return []
    return [list(getattr(snapshot, field_name)) for snapshot in result.retrieval_snapshots]


def _collect_snapshot_scalars(
    result: EvalResult | None,
    *,
    field_name: str,
) -> list[int]:
    if result is None:
        return []
    return [int(getattr(snapshot, field_name)) for snapshot in result.retrieval_snapshots]

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from book_research_agent.cli import run_eval, run_eval_compare
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.evaluation import (
    EvalCase,
    build_default_eval_run_path,
    build_eval_run_diff,
    get_latest_eval_run_paths,
    prune_auto_saved_eval_runs,
    read_eval_report_json,
    read_eval_cases_jsonl,
    run_eval_cases,
    summarize_eval_results,
)
from book_research_agent.core.indexing.models import IndexedChunk


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "auditor": [1.0, 0.0],
            "missing": [0.0, 0.0],
            "auditor language": [1.0, 0.0],
            "old man": [0.0, 1.0],
            "auditor as protector": [1.0, 0.0],
            "auditor as destroyer": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


class StubGenerationProvider:
    provider_name = "stub-generation"
    model_name = "stub-generation-model"

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        return "grounded stub answer"


def make_indexed_chunk(
    *,
    chunk_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
    embedding: list[float],
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=chunk_id.split(":", maxsplit=1)[0],
        text=text,
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=chunk_index,
            char_start=0,
            char_end=len(text),
        ),
        embedding=embedding,
        embedding_model="stub-model",
    )


def make_indexed_chunks() -> list[IndexedChunk]:
    return [
        make_indexed_chunk(
            chunk_id="doc-a:0",
            title="Auditor Notes",
            relative_path="notes/auditor.md",
            text="The auditor represents order.",
            chunk_index=0,
            embedding=[1.0, 0.0],
        ),
        make_indexed_chunk(
            chunk_id="doc-b:0",
            title="Old Man Notes",
            relative_path="notes/old-man.md",
            text="The old man preserves life.",
            chunk_index=0,
            embedding=[0.0, 1.0],
        ),
    ]


class GroundedEvalTests(unittest.TestCase):
    def test_read_eval_cases_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cases_path = Path(temp_dir) / "eval_cases.jsonl"
            cases_path.write_text(
                (
                    '{"id": "answer_1", "mode": "answer", '
                    '"query": "auditor", "notes": "smoke"}\n'
                ),
                encoding="utf-8",
            )

            cases = read_eval_cases_jsonl(cases_path)

        self.assertEqual(
            cases,
            [EvalCase(id="answer_1", mode="answer", query="auditor", notes="smoke")],
        )

    def test_run_eval_cases_reports_pass_warn_and_fail(self) -> None:
        warn_results = run_eval_cases(
            [
                EvalCase(id="answer_1", mode="answer", query="auditor"),
                EvalCase(id="canon_1", mode="canon", query="auditor language"),
            ],
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=2,
            warn_below=3,
        )
        fail_results = run_eval_cases(
            [EvalCase(id="missing_1", mode="answer", query="missing")],
            indexed_chunks=[],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=2,
            warn_below=3,
        )
        results = [*warn_results, *fail_results]
        summary = summarize_eval_results(results)

        self.assertEqual([result.status for result in results], ["WARN", "WARN", "FAIL"])
        self.assertEqual(results[0].message, "low retrieval")
        self.assertEqual(results[2].message, "no retrieval")
        self.assertEqual(
            results[0].retrieval_snapshots[0].top_paths,
            ["notes/auditor.md", "notes/old-man.md"],
        )
        self.assertEqual(
            results[0].retrieval_snapshots[0].top_chunk_ids,
            ["doc-a:0", "doc-b:0"],
        )
        self.assertEqual(results[0].retrieval_snapshots[0].top_scores, [1.0, 0.0])
        self.assertEqual(results[0].retrieval_snapshots[0].unique_document_count, 2)
        self.assertEqual(summary.warn_count, 2)
        self.assertEqual(summary.fail_count, 1)

    def test_run_eval_supports_pair_modes(self) -> None:
        results = run_eval_cases(
            [
                EvalCase(id="compare_1", mode="compare", query="auditor || old man"),
                EvalCase(
                    id="contradict_1",
                    mode="contradict",
                    query="auditor as protector || auditor as destroyer",
                ),
            ],
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=1,
            warn_below=1,
        )

        self.assertEqual([result.status for result in results], ["PASS", "PASS"])
        self.assertTrue(all(result.answer_present for result in results))
        self.assertEqual(len(results[0].retrieval_snapshots), 2)
        self.assertEqual(
            [snapshot.query for snapshot in results[0].retrieval_snapshots],
            ["auditor", "old man"],
        )

    def test_eval_cli_prints_results_and_summary(self) -> None:
        cases = [EvalCase(id="answer_1", mode="answer", query="auditor")]
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            settings = SimpleNamespace(
                data_dir=data_dir,
                data_index_dir=data_dir / "index",
            )
            args = argparse.Namespace(
                cases_file=Path("eval_cases.jsonl"),
                index_file=Path("chunk_index.jsonl"),
                top_k=1,
                json_out=None,
            )

            with patch(
                "book_research_agent.cli.load_settings",
                return_value=settings,
            ), patch(
                "book_research_agent.cli.read_eval_cases_jsonl",
                return_value=cases,
            ), patch(
                "book_research_agent.cli.read_indexed_chunks_jsonl",
                return_value=make_indexed_chunks(),
            ), patch(
                "book_research_agent.cli.create_embedding_provider",
                return_value=StubEmbeddingProvider(),
            ), patch(
                "book_research_agent.cli.create_generation_provider",
                return_value=StubGenerationProvider(),
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    exit_code = run_eval(args)

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[answer_1] WARN (low retrieval)", text)
        self.assertIn("retrieval_count: 1", text)
        self.assertIn("answer_present: yes", text)
        self.assertIn("top_paths: ['notes/auditor.md']", text)
        self.assertIn("top_chunk_ids: ['doc-a:0']", text)
        self.assertIn("saved_run:", text)
        self.assertIn("Summary:", text)
        self.assertIn("WARN: 1", text)

    def test_eval_cli_can_write_json_report(self) -> None:
        cases = [EvalCase(id="answer_1", mode="answer", query="auditor")]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "runs" / "eval.json"
            args = argparse.Namespace(
                cases_file=Path("eval_cases.jsonl"),
                index_file=Path("chunk_index.jsonl"),
                top_k=1,
                json_out=output_path,
            )
            settings = SimpleNamespace(
                data_dir=Path(temp_dir) / "data",
                data_index_dir=(Path(temp_dir) / "data" / "index"),
            )

            with patch(
                "book_research_agent.cli.load_settings",
                return_value=settings,
            ), patch(
                "book_research_agent.cli.read_eval_cases_jsonl",
                return_value=cases,
            ), patch(
                "book_research_agent.cli.read_indexed_chunks_jsonl",
                return_value=make_indexed_chunks(),
            ), patch(
                "book_research_agent.cli.create_embedding_provider",
                return_value=StubEmbeddingProvider(),
            ), patch(
                "book_research_agent.cli.create_generation_provider",
                return_value=StubGenerationProvider(),
            ):
                exit_code = run_eval(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            payload = output_path.read_text(encoding="utf-8")
            self.assertIn('"summary"', payload)
            self.assertIn('"results"', payload)
            self.assertIn('"top_paths"', payload)
            self.assertIn('"top_chunk_ids"', payload)

    def test_eval_helpers_prune_only_auto_saved_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runs_dir = Path(temp_dir)
            auto_one = runs_dir / "2026-04-25T13-20-10_eval.json"
            auto_two = runs_dir / "2026-04-25T13-20-11_eval.json"
            auto_three = runs_dir / "2026-04-25T13-20-12_eval.json"
            manual = runs_dir / "manual.json"

            for path in [auto_one, auto_two, auto_three, manual]:
                path.write_text("{}", encoding="utf-8")

            removed = prune_auto_saved_eval_runs(runs_dir, keep_last=2)

            self.assertEqual(removed, [auto_one])
            self.assertFalse(auto_one.exists())
            self.assertTrue(auto_two.exists())
            self.assertTrue(auto_three.exists())
            self.assertTrue(manual.exists())

    def test_build_default_eval_run_path_avoids_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runs_dir = Path(temp_dir)
            first = build_default_eval_run_path(
                runs_dir,
                now=datetime(2026, 4, 25, 13, 20, 10),
            )
            first.write_text("{}", encoding="utf-8")
            second = build_default_eval_run_path(
                runs_dir,
                now=datetime(2026, 4, 25, 13, 20, 10),
            )

            self.assertEqual(first.name, "2026-04-25T13-20-10_eval.json")
            self.assertEqual(second.name, "2026-04-25T13-20-11_eval.json")

    def test_eval_compare_latest_prints_diff_and_writes_json(self) -> None:
        cases = [EvalCase(id="answer_1", mode="answer", query="auditor")]
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            runs_dir = data_dir / "eval" / "runs"
            settings = SimpleNamespace(
                data_dir=data_dir,
                data_index_dir=data_dir / "index",
            )
            eval_args = argparse.Namespace(
                cases_file=Path("eval_cases.jsonl"),
                index_file=Path("chunk_index.jsonl"),
                top_k=1,
                json_out=None,
            )
            compare_args = argparse.Namespace(
                run_a=None,
                run_b=None,
                latest=True,
                json_out=runs_dir / "latest-diff.json",
            )

            with patch(
                "book_research_agent.cli.load_settings",
                return_value=settings,
            ), patch(
                "book_research_agent.cli.read_eval_cases_jsonl",
                return_value=cases,
            ), patch(
                "book_research_agent.cli.read_indexed_chunks_jsonl",
                return_value=make_indexed_chunks(),
            ), patch(
                "book_research_agent.cli.create_embedding_provider",
                return_value=StubEmbeddingProvider(),
            ), patch(
                "book_research_agent.cli.create_generation_provider",
                return_value=StubGenerationProvider(),
            ):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(run_eval(eval_args), 0)
                    self.assertEqual(run_eval(eval_args), 0)
                    compare_exit_code = run_eval_compare(compare_args)

            text = output.getvalue()
            self.assertEqual(compare_exit_code, 0)
            self.assertIn("book-research-agent eval-compare", text)
            self.assertIn("summary_delta:", text)
            self.assertIn("saved_diff:", text)
            self.assertTrue((runs_dir / "latest-diff.json").exists())

    def test_eval_run_diff_marks_changed_cases(self) -> None:
        before_report = read_eval_report_json(_write_report_fixture(status="WARN"))
        after_report = read_eval_report_json(_write_report_fixture(status="PASS"))

        diff = build_eval_run_diff(
            before_report,
            after_report,
            before_path=Path("before.json"),
            after_path=Path("after.json"),
        )

        self.assertEqual(diff.pass_delta, 1)
        self.assertEqual(diff.warn_delta, -1)
        self.assertEqual(len(diff.changed_cases), 1)
        self.assertEqual(diff.changed_cases[0].status_before, "WARN")
        self.assertEqual(diff.changed_cases[0].status_after, "PASS")

    def test_get_latest_eval_run_paths_ignores_non_report_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runs_dir = Path(temp_dir)
            first = runs_dir / "2026-04-25T13-20-10_eval.json"
            second = runs_dir / "2026-04-25T13-20-11_eval.json"
            diff_file = runs_dir / "latest-diff.json"

            _write_report_fixture(path=first)
            _write_report_fixture(path=second)
            diff_file.write_text('{"summary_delta": {"pass_delta": 1}}', encoding="utf-8")

            older, newer = get_latest_eval_run_paths(runs_dir)

            self.assertEqual(older, first)
            self.assertEqual(newer, second)


def _write_report_fixture(*, status: str = "WARN", path: Path | None = None) -> Path:
    if path is None:
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as temp_file:
            report_path = Path(temp_file.name)
    else:
        report_path = path

    report_payload = {
        "summary": {
            "pass_count": 1 if status == "PASS" else 0,
            "warn_count": 1 if status == "WARN" else 0,
            "fail_count": 0,
        },
        "results": [
            {
                "case_id": "answer_1",
                "mode": "answer",
                "status": status,
                "retrieval_count": 1,
                "answer_present": True,
                "message": "low retrieval" if status == "WARN" else "",
                "retrieval_snapshots": [
                    {
                        "query": "auditor",
                        "top_paths": ["notes/auditor.md"],
                        "top_titles": ["Auditor Notes"],
                        "top_chunk_ids": ["doc-a:0"],
                        "top_scores": [1.0],
                        "unique_document_count": 1,
                        "top_path_repeat_count": 1,
                        "duplicate_like_count": 0,
                        "score_spread": 0.0,
                    }
                ],
            }
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report_path


if __name__ == "__main__":
    unittest.main()

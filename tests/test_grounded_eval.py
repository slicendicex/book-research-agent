from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from book_research_agent.cli import run_eval
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.evaluation import (
    EvalCase,
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

    def generate_text(self, prompt: str) -> str:
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
        args = argparse.Namespace(
            cases_file=Path("eval_cases.jsonl"),
            index_file=Path("chunk_index.jsonl"),
            top_k=1,
            json_out=None,
        )

        with patch(
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

            with patch(
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


if __name__ == "__main__":
    unittest.main()

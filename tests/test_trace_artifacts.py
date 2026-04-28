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

from book_research_agent.cli import run_answer
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.tracing import (
    build_default_trace_path,
    run_answer_with_trace,
    run_compare_with_trace,
)


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "auditor question": [1.0, 0.0],
            "auditor": [1.0, 0.0],
            "old man": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


class StubGenerationProvider:
    provider_name = "stub-generation"
    model_name = "stub-generation-model"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_text(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if prompt.startswith("You select existing evidence chunks"):
            return '["R1"]'
        if prompt.startswith("You answer questions"):
            return "answer: The auditor represents oversight.\nsupport: Source 1 links the auditor to order.\nlimits: none"
        if prompt.startswith("You compare two topics"):
            return "shared_ground: both concern order\nkey_differences: one preserves, one judges\ntension: moderate\nlimits: none"
        return "stub output"


def make_indexed_chunk(
    *,
    chunk_id: str,
    document_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
    embedding: list[float],
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        text=text,
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=chunk_index,
            char_start=0,
            char_end=len(text),
        ),
        embedding=embedding,
        embedding_model="stub-embedding-model",
    )


def make_indexed_chunks() -> list[IndexedChunk]:
    return [
        make_indexed_chunk(
            chunk_id="doc-1:0",
            document_id="doc-1",
            title="Auditor Notes",
            relative_path="notes/auditor.md",
            text="The auditor represents oversight and order in the archive.",
            chunk_index=0,
            embedding=[1.0, 0.0],
        ),
        make_indexed_chunk(
            chunk_id="doc-2:0",
            document_id="doc-2",
            title="Old Man Notes",
            relative_path="notes/old-man.md",
            text="The old man preserves life and continuity in the forest.",
            chunk_index=0,
            embedding=[0.0, 1.0],
        ),
    ]


class TraceArtifactTests(unittest.TestCase):
    def test_run_answer_with_trace_captures_candidates_and_final_evidence(self) -> None:
        result, trace = run_answer_with_trace(
            query="auditor question",
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=1,
        )

        self.assertEqual(result.query, "auditor question")
        self.assertEqual(trace.mode, "answer")
        self.assertEqual(trace.query, "auditor question")
        self.assertEqual(len(trace.retrieval_candidates), 2)
        self.assertEqual(len(trace.final_evidence), 1)
        self.assertEqual(trace.final_evidence[0].chunk_id, "doc-1:0")
        self.assertIn("title: Auditor Notes", trace.final_evidence[0].evidence_block)
        self.assertIn("excerpt:", trace.final_evidence[0].evidence_block)
        self.assertIn("answer:", trace.generated_output)

    def test_run_compare_with_trace_uses_left_and_right_sections(self) -> None:
        result, trace = run_compare_with_trace(
            left_query="auditor",
            right_query="old man",
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=1,
        )

        self.assertEqual(result.left_query, "auditor")
        self.assertEqual(result.right_query, "old man")
        self.assertEqual(trace.mode, "compare")
        self.assertIsNone(trace.query)
        self.assertIsNotNone(trace.left)
        self.assertIsNotNone(trace.right)
        self.assertEqual(trace.left.query, "auditor")
        self.assertEqual(trace.right.query, "old man")
        self.assertEqual(len(trace.left.retrieval_candidates), 2)
        self.assertEqual(len(trace.right.final_evidence), 1)
        self.assertEqual(trace.left.final_evidence[0].chunk_id, "doc-1:0")
        self.assertEqual(trace.right.final_evidence[0].chunk_id, "doc-2:0")

    def test_build_default_trace_path_avoids_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            traces_dir = Path(temp_dir)
            first = build_default_trace_path(
                traces_dir,
                mode="answer",
                now=datetime(2026, 4, 28, 18, 20, 10),
            )
            first.write_text("{}", encoding="utf-8")
            second = build_default_trace_path(
                traces_dir,
                mode="answer",
                now=datetime(2026, 4, 28, 18, 20, 10),
            )

            self.assertEqual(first.name, "2026-04-28T18-20-10_answer_trace.json")
            self.assertEqual(second.name, "2026-04-28T18-20-11_answer_trace.json")

    def test_answer_cli_trace_out_writes_exact_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "manual-trace.json"
            settings = SimpleNamespace(
                data_dir=temp_path / "data",
                data_index_dir=temp_path / "data" / "index",
            )
            args = argparse.Namespace(
                query="auditor question",
                index_file=Path("chunk_index.jsonl"),
                top_k=1,
                save_trace=False,
                trace_out=output_path,
            )

            with patch(
                "book_research_agent.cli.load_settings",
                return_value=settings,
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
                    exit_code = run_answer(args)

            text = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertIn(f"saved_trace: {output_path}", text)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "answer")
            self.assertEqual(payload["query"], "auditor question")
            self.assertIn("generated_output", payload)
            self.assertIn("retrieval_candidates", payload)
            self.assertIn("final_evidence", payload)


if __name__ == "__main__":
    unittest.main()

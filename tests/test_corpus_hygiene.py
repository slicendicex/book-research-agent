from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from book_research_agent import cli
from book_research_agent.core.chunking.serialize import write_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk, ChunkMetadata
from book_research_agent.core.documents.models import Document, DocumentMetadata
from book_research_agent.core.hygiene import (
    find_duplicate_chunks,
    find_duplicate_documents,
    get_dedup_stats,
)
from book_research_agent.core.ingestion.serialize import write_documents_jsonl


def make_document(
    *,
    doc_id: str,
    relative_path: str,
    title: str,
    text: str,
) -> Document:
    return Document(
        id=doc_id,
        title=title,
        text=text,
        metadata=DocumentMetadata(
            source_kind="local_file",
            source_path=f"/tmp/{relative_path}",
            relative_path=relative_path,
            file_extension=Path(relative_path).suffix,
            content_sha1="sha1",
        ),
    )


def make_chunk(
    *,
    chunk_id: str,
    document_id: str,
    title: str,
    relative_path: str,
    text: str,
) -> Chunk:
    return Chunk(
        id=chunk_id,
        document_id=document_id,
        text=text,
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            char_start=0,
            char_end=len(text),
        ),
    )


class CorpusHygieneTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(sys, "argv", ["book-research-agent", *args]):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main()

        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_find_duplicate_documents_groups_exact_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            documents_path, _ = self.write_fixture_artifacts(Path(tmp_dir))

            groups = find_duplicate_documents(documents_path)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].similarity, 1.0)
        self.assertEqual(
            {item.relative_path for item in groups[0].items},
            {"notes/a.md", "notes/b.md"},
        )

    def test_find_duplicate_chunks_groups_near_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            _, chunks_path = self.write_fixture_artifacts(Path(tmp_dir))

            groups = find_duplicate_chunks(chunks_path)

        self.assertEqual(len(groups), 1)
        self.assertGreaterEqual(groups[0].similarity, 0.9)
        self.assertEqual(
            {item.item_id for item in groups[0].items},
            {"doc-1:0", "doc-2:0"},
        )

    def test_dedup_stats_counts_duplicate_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            documents_path, chunks_path = self.write_fixture_artifacts(Path(tmp_dir))

            stats = get_dedup_stats(documents_path, chunks_path)

        self.assertEqual(stats.document_count, 3)
        self.assertEqual(stats.chunk_count, 3)
        self.assertEqual(stats.duplicate_document_group_count, 1)
        self.assertEqual(stats.duplicate_chunk_group_count, 1)

    def test_cli_dedup_commands_report_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            documents_path, chunks_path = self.write_fixture_artifacts(Path(tmp_dir))

            stats_exit, stats_stdout, stats_stderr = self.run_cli(
                "dedup-stats",
                "--documents-file",
                str(documents_path),
                "--chunks-file",
                str(chunks_path),
            )
            docs_exit, docs_stdout, docs_stderr = self.run_cli(
                "find-duplicates",
                "--documents-file",
                str(documents_path),
            )
            chunks_exit, chunks_stdout, chunks_stderr = self.run_cli(
                "find-duplicate-chunks",
                "--chunks-file",
                str(chunks_path),
            )

        self.assertEqual(stats_exit, 0)
        self.assertEqual(stats_stderr, "")
        self.assertIn("duplicate_document_groups: 1", stats_stdout)
        self.assertIn("duplicate_chunk_groups: 1", stats_stdout)

        self.assertEqual(docs_exit, 0)
        self.assertEqual(docs_stderr, "")
        self.assertIn("book-research-agent find-duplicates", docs_stdout)
        self.assertIn("document_id: doc-1", docs_stdout)
        self.assertIn("path: notes/a.md", docs_stdout)

        self.assertEqual(chunks_exit, 0)
        self.assertEqual(chunks_stderr, "")
        self.assertIn("book-research-agent find-duplicate-chunks", chunks_stdout)
        self.assertIn("chunk_id: doc-1:0", chunks_stdout)
        self.assertIn("chunk_index: 0", chunks_stdout)

    @staticmethod
    def write_fixture_artifacts(root: Path) -> tuple[Path, Path]:
        documents_path = root / "documents.jsonl"
        chunks_path = root / "chunks.jsonl"

        documents = [
            make_document(
                doc_id="doc-1",
                relative_path="notes/a.md",
                title="A",
                text="Same text with spacing.",
            ),
            make_document(
                doc_id="doc-2",
                relative_path="notes/b.md",
                title="B",
                text="same   text with spacing.",
            ),
            make_document(
                doc_id="doc-3",
                relative_path="notes/c.md",
                title="C",
                text="Different material.",
            ),
        ]
        chunks = [
            make_chunk(
                chunk_id="doc-1:0",
                document_id="doc-1",
                title="A",
                relative_path="notes/a.md",
                text="alpha beta gamma delta epsilon",
            ),
            make_chunk(
                chunk_id="doc-2:0",
                document_id="doc-2",
                title="B",
                relative_path="notes/b.md",
                text="alpha beta gamma delta epsilon",
            ),
            make_chunk(
                chunk_id="doc-3:0",
                document_id="doc-3",
                title="C",
                relative_path="notes/c.md",
                text="zeta eta theta",
            ),
        ]

        write_documents_jsonl(documents, documents_path)
        write_chunks_jsonl(chunks, chunks_path)
        return documents_path, chunks_path


if __name__ == "__main__":
    unittest.main()

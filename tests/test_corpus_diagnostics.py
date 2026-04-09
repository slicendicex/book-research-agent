from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from book_research_agent import cli
from book_research_agent.core.chunks.models import Chunk, ChunkMetadata
from book_research_agent.core.chunking.serialize import write_chunks_jsonl
from book_research_agent.core.documents.models import Document, DocumentMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.indexing.serialize import write_indexed_chunks_jsonl
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


def make_indexed_chunk(
    *,
    chunk_id: str,
    document_id: str,
    title: str,
    relative_path: str,
    text: str,
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        text=text,
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            char_start=0,
            char_end=len(text),
        ),
        embedding=[0.1, 0.2, 0.3],
        embedding_model="embed-v4.0",
    )


class CorpusDiagnosticsTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(sys, "argv", ["book-research-agent", *args]):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = cli.main()

        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_stats_reports_counts_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents_path, chunks_path, index_path = self.write_fixture_artifacts(root)

            exit_code, stdout, stderr = self.run_cli(
                "stats",
                "--documents-file",
                str(documents_path),
                "--chunks-file",
                str(chunks_path),
                "--index-file",
                str(index_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("book-research-agent stats", stdout)
        self.assertIn(f"documents_path: {documents_path}", stdout)
        self.assertIn("documents: 1", stdout)
        self.assertIn("chunks: 1", stdout)
        self.assertIn("indexed_chunks: 1", stdout)

    def test_inspect_doc_displays_document_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents_path, _, _ = self.write_fixture_artifacts(root)

            exit_code, stdout, stderr = self.run_cli(
                "inspect-doc",
                "--path",
                "notes/example.md",
                "--documents-file",
                str(documents_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("book-research-agent inspect-doc", stdout)
        self.assertIn("title: Example", stdout)
        self.assertIn("path: notes/example.md", stdout)
        self.assertIn("char_count: 11", stdout)
        self.assertIn("hello world", stdout)

    def test_inspect_chunk_displays_required_metadata_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _, chunks_path, _ = self.write_fixture_artifacts(root)

            exit_code, stdout, stderr = self.run_cli(
                "inspect-chunk",
                "--chunk-id",
                "doc-1:0",
                "--chunks-file",
                str(chunks_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("chunk_id: doc-1:0", stdout)
        self.assertIn("document_id: doc-1", stdout)
        self.assertIn("title: Example", stdout)
        self.assertIn("path: notes/example.md", stdout)
        self.assertIn("char_start: 0", stdout)
        self.assertIn("char_end: 11", stdout)
        self.assertIn("hello world", stdout)

    def test_inspect_index_omits_full_embedding_vector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _, _, index_path = self.write_fixture_artifacts(root)

            exit_code, stdout, stderr = self.run_cli(
                "inspect-index",
                "--chunk-id",
                "doc-1:0",
                "--index-file",
                str(index_path),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("book-research-agent inspect-index", stdout)
        self.assertIn("embedding_model: embed-v4.0", stdout)
        self.assertIn("embedding_dimension: 3", stdout)
        self.assertIn("path: notes/example.md", stdout)
        self.assertNotIn("[0.1, 0.2, 0.3]", stdout)

    def test_missing_file_returns_direct_error_and_non_zero_exit(self) -> None:
        missing_path = Path("/tmp/does-not-exist-documents.jsonl")

        exit_code, stdout, stderr = self.run_cli(
            "stats",
            "--documents-file",
            str(missing_path),
            "--chunks-file",
            str(missing_path),
            "--index-file",
            str(missing_path),
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn(f"file not found: {missing_path}", stderr)

    def test_directory_path_returns_direct_error_and_non_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)

            exit_code, stdout, stderr = self.run_cli(
                "stats",
                "--documents-file",
                str(root),
                "--chunks-file",
                str(root),
                "--index-file",
                str(root),
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn(f"file not found: {root}", stderr)

    def test_not_found_returns_direct_error_and_non_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents_path, _, _ = self.write_fixture_artifacts(root)

            exit_code, stdout, stderr = self.run_cli(
                "inspect-doc",
                "--path",
                "notes/missing.md",
                "--documents-file",
                str(documents_path),
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("document not found: notes/missing.md", stderr)

    @staticmethod
    def write_fixture_artifacts(root: Path) -> tuple[Path, Path, Path]:
        documents_path = root / "documents.jsonl"
        chunks_path = root / "chunks.jsonl"
        index_path = root / "chunk_index.jsonl"

        document = make_document(
            doc_id="doc-1",
            relative_path="notes/example.md",
            title="Example",
            text="hello world",
        )
        chunk = make_chunk(
            chunk_id="doc-1:0",
            document_id="doc-1",
            title="Example",
            relative_path="notes/example.md",
            text="hello world",
        )
        indexed_chunk = make_indexed_chunk(
            chunk_id="doc-1:0",
            document_id="doc-1",
            title="Example",
            relative_path="notes/example.md",
            text="hello world",
        )

        write_documents_jsonl([document], documents_path)
        write_chunks_jsonl([chunk], chunks_path)
        write_indexed_chunks_jsonl([indexed_chunk], index_path)
        return documents_path, chunks_path, index_path


if __name__ == "__main__":
    unittest.main()

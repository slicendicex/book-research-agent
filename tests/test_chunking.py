from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from book_research_agent.core.chunking import chunk_documents, write_chunks_jsonl
from book_research_agent.core.documents.models import Document, DocumentMetadata
from book_research_agent.core.ingestion.serialize import read_documents_jsonl, write_documents_jsonl


def make_document(doc_id: str, text: str, title: str = "Doc") -> Document:
    return Document(
        id=doc_id,
        title=title,
        text=text,
        metadata=DocumentMetadata(
            source_kind="local_file",
            source_path=f"/tmp/{doc_id}.txt",
            relative_path=f"{doc_id}.txt",
            file_extension=".txt",
            content_sha1="sha1",
        ),
    )


class ChunkingTests(unittest.TestCase):
    def test_short_document_produces_one_chunk(self) -> None:
        document = make_document("doc-1", "short text")

        chunks = chunk_documents([document], chunk_size=50, chunk_overlap=10)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].id, "doc-1:0")
        self.assertEqual(chunks[0].metadata.char_start, 0)
        self.assertEqual(chunks[0].metadata.char_end, len("short text"))

    def test_long_document_produces_multiple_chunks_with_overlap(self) -> None:
        document = make_document("doc-2", "abcdefghij", title="Example")

        chunks = chunk_documents([document], chunk_size=4, chunk_overlap=1)

        self.assertEqual([chunk.text for chunk in chunks], ["abcd", "defg", "ghij"])
        self.assertEqual(chunks[1].metadata.char_start, 3)
        self.assertEqual(chunks[1].metadata.char_end, 7)
        self.assertEqual(chunks[1].metadata.document_relative_path, "doc-2.txt")
        self.assertEqual(chunks[1].metadata.source_title, "Example")

    def test_invalid_overlap_raises_clear_error(self) -> None:
        document = make_document("doc-3", "text")

        with self.assertRaisesRegex(
            ValueError,
            "chunk_overlap must be smaller than chunk_size",
        ):
            chunk_documents([document], chunk_size=10, chunk_overlap=10)

    def test_jsonl_output_is_produced_from_documents_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            documents_path = root / "documents.jsonl"
            chunks_path = root / "chunks.jsonl"
            documents = [
                make_document("doc-4", "abcdef", title="Alpha"),
                make_document("doc-5", "uvwxyz", title="Beta"),
            ]

            write_documents_jsonl(documents, documents_path)
            loaded_documents = read_documents_jsonl(documents_path)
            chunks = chunk_documents(loaded_documents, chunk_size=4, chunk_overlap=1)
            write_chunks_jsonl(chunks, chunks_path)

            self.assertTrue(chunks_path.exists())
            lines = chunks_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 4)

            payload = [json.loads(line) for line in lines]
            self.assertEqual(payload[0]["document_id"], "doc-4")
            self.assertEqual(payload[0]["metadata"]["source_title"], "Alpha")


if __name__ == "__main__":
    unittest.main()

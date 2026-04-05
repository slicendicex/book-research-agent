from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from book_research_agent.core.ingestion import ingest_documents, write_documents_jsonl


class DocumentIngestionTests(unittest.TestCase):
    def test_ingests_txt_and_md_and_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            raw_dir = root / "raw"
            raw_dir.mkdir()

            (raw_dir / "notes.txt").write_text("Hello\r\nworld", encoding="utf-8")
            (raw_dir / "chapter.md").write_text(
                "# Chapter One\n\nBody text",
                encoding="utf-8",
            )
            (raw_dir / "ignore.pdf").write_text("not supported", encoding="utf-8")

            result = ingest_documents(raw_dir)

            self.assertEqual(result.scanned_files, 3)
            self.assertEqual(result.supported_files, 2)
            self.assertEqual(result.skipped_files, 1)
            self.assertEqual(result.produced_documents, 2)

            documents_by_path = {
                document.metadata.relative_path: document for document in result.documents
            }
            self.assertEqual(documents_by_path["notes.txt"].title, "notes")
            self.assertEqual(documents_by_path["notes.txt"].text, "Hello\nworld")
            self.assertEqual(documents_by_path["chapter.md"].title, "Chapter One")

            output_path = root / "processed" / "documents.jsonl"
            write_documents_jsonl(result.documents, output_path)

            self.assertTrue(output_path.exists())
            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)

            payload = [json.loads(line) for line in lines]
            self.assertEqual({item["title"] for item in payload}, {"notes", "Chapter One"})


if __name__ == "__main__":
    unittest.main()

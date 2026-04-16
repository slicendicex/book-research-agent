from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from book_research_agent.cli import run_corpus_report
from book_research_agent.core.chunking.serialize import write_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk, ChunkMetadata
from book_research_agent.core.corpus_report import build_corpus_report
from book_research_agent.core.documents.models import Document, DocumentMetadata
from book_research_agent.core.ingestion.serialize import write_documents_jsonl


def make_document(
    doc_id: str,
    title: str,
    relative_path: str,
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
            file_extension=".txt",
            content_sha1=f"sha1-{doc_id}",
        ),
    )


def make_chunk(
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


class CorpusReportTests(unittest.TestCase):
    def test_corpus_report_surfaces_motifs_and_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            documents_path, chunks_path = self.write_fixture_artifacts(Path(temp_dir))

            report = build_corpus_report(
                documents_path,
                chunks_path,
                top_limit=3,
                emerging_limit=10,
                orphan_limit=10,
            )

        top_motifs = {motif.text for motif in report.top_motifs}
        emerging_motifs = {motif.text for motif in report.emerging_motifs}
        orphan_paths = {note.relative_path for note in report.orphan_notes}

        self.assertIn("auditor", top_motifs)
        self.assertIn("ritual", emerging_motifs)
        self.assertIn("notes/orphan.txt", orphan_paths)

    def test_corpus_report_cli_prints_readable_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            documents_path, chunks_path = self.write_fixture_artifacts(Path(temp_dir))
            args = argparse.Namespace(
                documents_file=documents_path,
                chunks_file=chunks_path,
                top_limit=3,
                emerging_limit=5,
                orphan_limit=5,
            )

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = run_corpus_report(args)

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("book-research-agent corpus-report", text)
        self.assertIn("Top motifs:", text)
        self.assertIn("Emerging motifs:", text)
        self.assertIn("Potential orphan notes:", text)
        self.assertIn("- auditor", text)
        self.assertIn("notes/orphan.txt", text)
        self.assertNotIn("chunk_count", text)
        self.assertNotIn("chunks:", text)

    def write_fixture_artifacts(self, root: Path) -> tuple[Path, Path]:
        documents_path = root / "documents.jsonl"
        chunks_path = root / "chunks.jsonl"
        documents = [
            make_document(
                "doc-1",
                "Auditor One",
                "notes/auditor-one.txt",
                "auditor auditor order museum control forest ritual",
            ),
            make_document(
                "doc-2",
                "Auditor Two",
                "notes/auditor-two.txt",
                "auditor auditor order museum control old man forest ritual",
            ),
            make_document(
                "doc-3",
                "Orphan",
                "notes/orphan.txt",
                "starship quantum nebula engine isolated",
            ),
        ]
        chunks = [
            make_chunk(
                "doc-1:0",
                "doc-1",
                "Auditor One",
                "notes/auditor-one.txt",
                documents[0].text,
            ),
            make_chunk(
                "doc-2:0",
                "doc-2",
                "Auditor Two",
                "notes/auditor-two.txt",
                documents[1].text,
            ),
            make_chunk(
                "doc-3:0",
                "doc-3",
                "Orphan",
                "notes/orphan.txt",
                documents[2].text,
            ),
        ]
        write_documents_jsonl(documents, documents_path)
        write_chunks_jsonl(chunks, chunks_path)
        return documents_path, chunks_path


if __name__ == "__main__":
    unittest.main()

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
    def test_corpus_report_surfaces_concepts_co_occurrences_and_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            documents_path, chunks_path = self.write_fixture_artifacts(Path(temp_dir))

            report = build_corpus_report(
                documents_path,
                chunks_path,
                top_limit=3,
                emerging_limit=10,
                orphan_limit=10,
            )

        core_concepts = {concept.text for concept in report.core_concepts}
        secondary_concepts = {concept.text for concept in report.secondary_concepts}
        co_occurrences = {
            (pair.left, pair.right)
            for pair in report.co_occurrences
        }
        orphan_paths = {note.relative_path for note in report.orphan_notes}

        self.assertIn("AUDITOR", core_concepts)
        self.assertIn("RITUAL", secondary_concepts)
        self.assertIn(("AUDITOR", "FOREST"), co_occurrences)
        self.assertIn("notes/orphan.txt", orphan_paths)

    def test_corpus_report_normalizes_russian_word_forms(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            documents_path = root / "documents.jsonl"
            chunks_path = root / "chunks.jsonl"
            documents = [
                make_document(
                    "doc-1",
                    "Аудитор",
                    "notes/auditor-one.txt",
                    "аудитор аудитора старик старика музей системы",
                ),
                make_document(
                    "doc-2",
                    "Старик",
                    "notes/auditor-two.txt",
                    "аудитором аудитору стариком старику музея систему",
                ),
            ]
            chunks = [
                make_chunk(
                    "doc-1:0",
                    "doc-1",
                    documents[0].title,
                    documents[0].metadata.relative_path,
                    documents[0].text,
                ),
                make_chunk(
                    "doc-2:0",
                    "doc-2",
                    documents[1].title,
                    documents[1].metadata.relative_path,
                    documents[1].text,
                ),
            ]
            write_documents_jsonl(documents, documents_path)
            write_chunks_jsonl(chunks, chunks_path)

            report = build_corpus_report(
                documents_path,
                chunks_path,
                top_limit=10,
                emerging_limit=10,
                orphan_limit=10,
            )

        concepts = {concept.text: concept for concept in report.core_concepts}
        self.assertEqual(concepts["АУДИТОР"].occurrences, 4)
        self.assertEqual(concepts["СТАРИК"].occurrences, 4)
        self.assertEqual(concepts["МУЗЕЙ"].document_count, 2)
        self.assertNotIn("СИСТЕМА", concepts)

    def test_corpus_report_filters_non_noun_russian_noise(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            documents_path = root / "documents.jsonl"
            chunks_path = root / "chunks.jsonl"
            documents = [
                make_document(
                    "doc-1",
                    "Noise One",
                    "notes/noise-one.txt",
                    "аудитора земли земле видит первый прав",
                ),
                make_document(
                    "doc-2",
                    "Noise Two",
                    "notes/noise-two.txt",
                    "аудитором землёй земля видит первый прав",
                ),
            ]
            chunks = [
                make_chunk(
                    "doc-1:0",
                    "doc-1",
                    documents[0].title,
                    documents[0].metadata.relative_path,
                    documents[0].text,
                ),
                make_chunk(
                    "doc-2:0",
                    "doc-2",
                    documents[1].title,
                    documents[1].metadata.relative_path,
                    documents[1].text,
                ),
            ]
            write_documents_jsonl(documents, documents_path)
            write_chunks_jsonl(chunks, chunks_path)

            report = build_corpus_report(
                documents_path,
                chunks_path,
                top_limit=10,
                emerging_limit=10,
                orphan_limit=10,
            )

        concepts = {concept.text: concept for concept in report.core_concepts}
        self.assertEqual(concepts["АУДИТОР"].document_count, 2)
        self.assertEqual(concepts["ЗЕМЛЯ"].occurrences, 4)
        self.assertNotIn("ВИДЕТЬ", concepts)
        self.assertNotIn("ПЕРВЫЙ", concepts)
        self.assertNotIn("ПРАВО", concepts)

    def test_corpus_report_applies_project_concept_stoplist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            documents_path = root / "documents.jsonl"
            chunks_path = root / "chunks.jsonl"
            stoplist_path = root / "concept_stoplist.txt"
            documents = [
                make_document(
                    "doc-1",
                    "Concept One",
                    "notes/concept-one.txt",
                    "аудитор идея идея музей ритуал",
                ),
                make_document(
                    "doc-2",
                    "Concept Two",
                    "notes/concept-two.txt",
                    "аудитор идеи музея ритуал",
                ),
                make_document(
                    "doc-3",
                    "Concept Three",
                    "notes/concept-three.txt",
                    "аудитор идея лес",
                ),
            ]
            chunks = [
                make_chunk(
                    f"{document.id}:0",
                    document.id,
                    document.title,
                    document.metadata.relative_path,
                    document.text,
                )
                for document in documents
            ]
            write_documents_jsonl(documents, documents_path)
            write_chunks_jsonl(chunks, chunks_path)
            stoplist_path.write_text("идея\n", encoding="utf-8")

            report = build_corpus_report(
                documents_path,
                chunks_path,
                concept_stoplist_path=stoplist_path,
                top_limit=10,
                emerging_limit=10,
                orphan_limit=10,
            )

        core_concepts = {concept.text for concept in report.core_concepts}
        secondary_concepts = {concept.text for concept in report.secondary_concepts}
        co_occurrence_concepts = {
            concept
            for pair in report.co_occurrences
            for concept in (pair.left, pair.right)
        }

        self.assertIn("АУДИТОР", core_concepts)
        self.assertNotIn("ИДЕЯ", core_concepts)
        self.assertNotIn("ИДЕЯ", secondary_concepts)
        self.assertNotIn("ИДЕЯ", co_occurrence_concepts)

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
        self.assertIn("Core concepts:", text)
        self.assertIn("Secondary concept lines:", text)
        self.assertIn("Strong co-occurrences:", text)
        self.assertIn("Potential orphan notes:", text)
        self.assertIn("- AUDITOR", text)
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

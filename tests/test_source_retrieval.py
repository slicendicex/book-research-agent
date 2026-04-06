from __future__ import annotations

import unittest

from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval import SearchResult
from book_research_agent.core.retrieval.source import (
    SourceResult,
    build_source_results,
    filter_neighboring_results,
    format_excerpt,
)


def make_search_result(
    *,
    chunk_id: str,
    document_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
    char_start: int = 0,
    score: float = 1.0,
) -> SearchResult:
    return SearchResult(
        indexed_chunk=IndexedChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            text=text,
            metadata=ChunkMetadata(
                document_relative_path=relative_path,
                source_title=title,
                chunk_index=chunk_index,
                char_start=char_start,
                char_end=char_start + len(text),
            ),
            embedding=[1.0, 0.0],
            embedding_model="embed-v4.0",
        ),
        score=score,
    )


class SourceRetrievalTests(unittest.TestCase):
    def test_format_excerpt_normalizes_whitespace(self) -> None:
        excerpt = format_excerpt("  Alpha\n\nbeta\t gamma  ", max_length=80)
        self.assertEqual(excerpt, "Alpha beta gamma")

    def test_format_excerpt_truncates_at_word_boundary_with_ellipsis(self) -> None:
        excerpt = format_excerpt(
            "alpha beta gamma delta epsilon zeta",
            max_length=20,
        )

        self.assertEqual(excerpt, "alpha beta gamma...")

    def test_format_excerpt_can_trim_start_word_for_mid_chunk_display(self) -> None:
        excerpt = format_excerpt(
            "fragment continues with readable text",
            max_length=80,
            trim_start_word=True,
        )

        self.assertEqual(excerpt, "... continues with readable text")

    def test_filter_neighboring_results_suppresses_close_same_document_chunks(self) -> None:
        search_results = [
            make_search_result(
                chunk_id="doc-1:2",
                document_id="doc-1",
                title="Alpha",
                relative_path="alpha.md",
                text="alpha body",
                chunk_index=2,
                score=0.99,
            ),
            make_search_result(
                chunk_id="doc-1:3",
                document_id="doc-1",
                title="Alpha",
                relative_path="alpha.md",
                text="alpha nearby",
                chunk_index=3,
                score=0.95,
            ),
            make_search_result(
                chunk_id="doc-2:0",
                document_id="doc-2",
                title="Beta",
                relative_path="beta.md",
                text="beta body",
                chunk_index=0,
                score=0.90,
            ),
        ]

        filtered = filter_neighboring_results(search_results, neighbor_window=1)

        self.assertEqual(
            [result.indexed_chunk.chunk_id for result in filtered],
            ["doc-1:2", "doc-2:0"],
        )

    def test_build_source_results_shapes_display_output_without_mutating_chunk_text(self) -> None:
        search_result = make_search_result(
            chunk_id="doc-1:1",
            document_id="doc-1",
            title="Alpha",
            relative_path="alpha.md",
            text="fragment continues with readable text",
            chunk_index=1,
            char_start=5,
            score=0.88,
        )

        source_results = build_source_results(
            [search_result],
            max_results=1,
            excerpt_length=80,
        )

        self.assertEqual(
            source_results,
            [
                SourceResult(
                    score=0.88,
                    title="Alpha",
                    relative_path="alpha.md",
                    chunk_index=1,
                    excerpt="... continues with readable text",
                )
            ],
        )
        self.assertEqual(
            search_result.indexed_chunk.text,
            "fragment continues with readable text",
        )


if __name__ == "__main__":
    unittest.main()

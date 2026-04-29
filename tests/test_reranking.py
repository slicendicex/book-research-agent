from __future__ import annotations

import unittest

from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval import (
    SearchResult,
    build_reranking_prompt,
    parse_candidate_id_order,
    rerank_search_results,
)


class StubGenerationProvider:
    provider_name = "stub-generation"
    model_name = "stub-generation-model"

    def __init__(self, response: str, *, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.prompts: list[str] = []

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        self.prompts.append(prompt)
        if self.fail:
            raise RuntimeError("rerank failure")
        return self.response


def make_search_result(
    *,
    chunk_id: str,
    title: str,
    relative_path: str,
    text: str,
    score: float,
) -> SearchResult:
    return SearchResult(
        indexed_chunk=IndexedChunk(
            chunk_id=chunk_id,
            document_id=chunk_id.split(":", maxsplit=1)[0],
            text=text,
            metadata=ChunkMetadata(
                document_relative_path=relative_path,
                source_title=title,
                chunk_index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
                char_start=0,
                char_end=len(text),
            ),
            embedding=[1.0, 0.0],
            embedding_model="stub-model",
        ),
        score=score,
    )


def make_candidates() -> list[SearchResult]:
    return [
        make_search_result(
            chunk_id="doc-a:0",
            title="Alpha",
            relative_path="notes/alpha.md",
            text="Alpha is related but less useful.",
            score=0.95,
        ),
        make_search_result(
            chunk_id="doc-b:0",
            title="Beta",
            relative_path="notes/beta.md",
            text="Beta is the most complete evidence.",
            score=0.91,
        ),
        make_search_result(
            chunk_id="doc-c:0",
            title="Gamma",
            relative_path="notes/gamma.md",
            text="Gamma provides fallback context.",
            score=0.84,
        ),
    ]


class RerankingTests(unittest.TestCase):
    def test_build_reranking_prompt_contains_query_ids_and_sources(self) -> None:
        prompt = build_reranking_prompt(
            query="alpha question",
            candidates=make_candidates()[:2],
        )

        self.assertIn("Return only a JSON array of candidate ids", prompt)
        self.assertIn("Query: alpha question", prompt)
        self.assertIn("id: R1", prompt)
        self.assertIn("id: R2", prompt)
        self.assertIn("chunk_id: doc-a:0", prompt)
        self.assertIn("path: notes/beta.md", prompt)
        self.assertIn("title: Beta", prompt)
        self.assertIn("Do not explain", prompt)

    def test_parse_candidate_id_order_accepts_json_and_plain_ids(self) -> None:
        self.assertEqual(
            parse_candidate_id_order('["R2", "R1"]'),
            ["R2", "R1"],
        )
        self.assertEqual(
            parse_candidate_id_order("R3\nR1"),
            ["R3", "R1"],
        )

    def test_parse_candidate_id_order_rejects_verbose_output(self) -> None:
        self.assertEqual(
            parse_candidate_id_order("The best order is R2, then R1."),
            [],
        )

    def test_rerank_search_results_reorders_existing_candidates(self) -> None:
        candidates = make_candidates()

        results = rerank_search_results(
            query="alpha question",
            candidates=candidates,
            generation_provider=StubGenerationProvider('["R2", "R1"]'),
            top_k=2,
        )

        self.assertEqual(
            [result.indexed_chunk.chunk_id for result in results],
            ["doc-b:0", "doc-a:0"],
        )
        self.assertIs(results[0], candidates[1])

    def test_rerank_search_results_ignores_unknown_and_duplicate_ids(self) -> None:
        results = rerank_search_results(
            query="alpha question",
            candidates=make_candidates(),
            generation_provider=StubGenerationProvider('["R2", "R9", "R2"]'),
            top_k=3,
        )

        self.assertEqual(
            [result.indexed_chunk.chunk_id for result in results],
            ["doc-b:0", "doc-a:0", "doc-c:0"],
        )

    def test_rerank_search_results_falls_back_on_malformed_output(self) -> None:
        results = rerank_search_results(
            query="alpha question",
            candidates=make_candidates(),
            generation_provider=StubGenerationProvider("I would choose R2."),
            top_k=2,
        )

        self.assertEqual(
            [result.indexed_chunk.chunk_id for result in results],
            ["doc-a:0", "doc-b:0"],
        )

    def test_rerank_search_results_falls_back_on_generation_failure(self) -> None:
        results = rerank_search_results(
            query="alpha question",
            candidates=make_candidates(),
            generation_provider=StubGenerationProvider("", fail=True),
            top_k=2,
        )

        self.assertEqual(
            [result.indexed_chunk.chunk_id for result in results],
            ["doc-a:0", "doc-b:0"],
        )


if __name__ == "__main__":
    unittest.main()

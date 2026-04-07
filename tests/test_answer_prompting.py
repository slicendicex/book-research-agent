from __future__ import annotations

import unittest

from book_research_agent.core.answering import build_grounded_answer_prompt
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval import SearchResult


def make_search_result(
    *,
    chunk_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
) -> SearchResult:
    return SearchResult(
        indexed_chunk=IndexedChunk(
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
            embedding=[1.0, 0.0],
            embedding_model="embed-v4.0",
        ),
        score=0.95,
    )


class AnswerPromptingTests(unittest.TestCase):
    def test_prompt_includes_query_instruction_and_sources(self) -> None:
        prompt = build_grounded_answer_prompt(
            query="What does the auditor represent?",
            search_results=[
                make_search_result(
                    chunk_id="doc-1:0",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor represents oversight and accountability.",
                    chunk_index=0,
                )
            ],
        )

        self.assertIn("Question: What does the auditor represent?", prompt)
        self.assertIn("using only the provided sources", prompt)
        self.assertIn("title: Auditor Notes", prompt)
        self.assertIn("path: notes/auditor.md", prompt)
        self.assertIn("chunk_index: 0", prompt)
        self.assertIn(
            "content: The auditor represents oversight and accountability.",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()

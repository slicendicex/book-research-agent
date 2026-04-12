from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk
from book_research_agent.core.documents.models import Document
from book_research_agent.core.ingestion.serialize import read_documents_jsonl


NEAR_DUPLICATE_THRESHOLD = 0.9


@dataclass(frozen=True)
class DuplicateItem:
    item_id: str
    document_id: str
    title: str
    relative_path: str
    chunk_index: int | None


@dataclass(frozen=True)
class DuplicateGroup:
    similarity: float
    items: list[DuplicateItem]


@dataclass(frozen=True)
class DedupStats:
    document_count: int
    chunk_count: int
    duplicate_document_group_count: int
    duplicate_chunk_group_count: int


def get_dedup_stats(documents_path: Path, chunks_path: Path) -> DedupStats:
    documents = _read_documents(documents_path)
    chunks = _read_chunks(chunks_path)
    return DedupStats(
        document_count=len(documents),
        chunk_count=len(chunks),
        duplicate_document_group_count=len(_find_duplicate_document_groups(documents)),
        duplicate_chunk_group_count=len(_find_duplicate_chunk_groups(chunks)),
    )


def find_duplicate_documents(documents_path: Path) -> list[DuplicateGroup]:
    return _find_duplicate_document_groups(_read_documents(documents_path))


def find_duplicate_chunks(chunks_path: Path) -> list[DuplicateGroup]:
    return _find_duplicate_chunk_groups(_read_chunks(chunks_path))


def _find_duplicate_document_groups(documents: list[Document]) -> list[DuplicateGroup]:
    items = [
        (
            DuplicateItem(
                item_id=document.id,
                document_id=document.id,
                title=document.title,
                relative_path=document.metadata.relative_path,
                chunk_index=None,
            ),
            document.text,
        )
        for document in documents
    ]
    return _find_duplicate_groups(items)


def _find_duplicate_chunk_groups(chunks: list[Chunk]) -> list[DuplicateGroup]:
    items = [
        (
            DuplicateItem(
                item_id=chunk.id,
                document_id=chunk.document_id,
                title=chunk.metadata.source_title,
                relative_path=chunk.metadata.document_relative_path,
                chunk_index=chunk.metadata.chunk_index,
            ),
            chunk.text,
        )
        for chunk in chunks
    ]
    return _find_duplicate_groups(items)


def _find_duplicate_groups(
    items: list[tuple[DuplicateItem, str]],
) -> list[DuplicateGroup]:
    exact_groups = _find_exact_duplicate_groups(items)
    grouped_item_ids = {
        item.item_id
        for group in exact_groups
        for item in group.items
    }
    near_groups = _find_near_duplicate_groups(
        [
            (item, text)
            for item, text in items
            if item.item_id not in grouped_item_ids
        ]
    )
    return exact_groups + near_groups


def _find_exact_duplicate_groups(
    items: list[tuple[DuplicateItem, str]],
) -> list[DuplicateGroup]:
    groups_by_text: dict[str, list[DuplicateItem]] = {}
    for item, text in items:
        normalized_text = _normalize_for_duplicate_detection(text)
        if not normalized_text:
            continue
        groups_by_text.setdefault(normalized_text, []).append(item)

    return [
        DuplicateGroup(similarity=1.0, items=group_items)
        for group_items in groups_by_text.values()
        if len(group_items) > 1
    ]


def _find_near_duplicate_groups(
    items: list[tuple[DuplicateItem, str]],
) -> list[DuplicateGroup]:
    groups: list[DuplicateGroup] = []
    used_item_ids: set[str] = set()
    tokenized_items = [
        (item, _tokenize_for_similarity(text))
        for item, text in items
    ]

    for index, (item, tokens) in enumerate(tokenized_items):
        if item.item_id in used_item_ids or not tokens:
            continue

        group_items = [item]
        best_similarity = 0.0

        for other_item, other_tokens in tokenized_items[index + 1 :]:
            if other_item.item_id in used_item_ids or not other_tokens:
                continue

            similarity = _jaccard_similarity(tokens, other_tokens)
            if similarity >= NEAR_DUPLICATE_THRESHOLD:
                group_items.append(other_item)
                best_similarity = max(best_similarity, similarity)

        if len(group_items) > 1:
            used_item_ids.update(group_item.item_id for group_item in group_items)
            groups.append(
                DuplicateGroup(
                    similarity=best_similarity,
                    items=group_items,
                )
            )

    return groups


def _normalize_for_duplicate_detection(text: str) -> str:
    return " ".join(text.lower().split())


def _tokenize_for_similarity(text: str) -> set[str]:
    normalized_text = _normalize_for_duplicate_detection(text)
    return set(re.findall(r"\w+", normalized_text))


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _read_documents(documents_path: Path) -> list[Document]:
    _require_file(documents_path)
    return read_documents_jsonl(documents_path)


def _read_chunks(chunks_path: Path) -> list[Chunk]:
    _require_file(chunks_path)
    return read_chunks_jsonl(chunks_path)


def _require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")

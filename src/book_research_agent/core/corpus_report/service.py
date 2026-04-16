from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk
from book_research_agent.core.corpus_report.models import (
    CorpusReport,
    MotifCandidate,
    OrphanNote,
)
from book_research_agent.core.documents.models import Document
from book_research_agent.core.ingestion.serialize import read_documents_jsonl


STOPWORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "not",
    "that",
    "the",
    "this",
    "with",
    "без",
    "его",
    "будет",
    "было",
    "быть",
    "все",
    "всё",
    "для",
    "есть",
    "еще",
    "ещё",
    "если",
    "или",
    "как",
    "когда",
    "который",
    "может",
    "один",
    "одна",
    "одно",
    "одного",
    "она",
    "они",
    "перед",
    "после",
    "потому",
    "просто",
    "себя",
    "свои",
    "свой",
    "свою",
    "так",
    "там",
    "только",
    "уже",
    "что",
    "чтобы",
    "через",
    "этот",
    "это",
}


def build_corpus_report(
    documents_path: Path,
    chunks_path: Path,
    *,
    top_limit: int = 10,
    emerging_limit: int = 10,
    orphan_limit: int = 10,
    orphan_threshold: float = 0.08,
) -> CorpusReport:
    documents = read_documents_jsonl(documents_path)
    chunks = read_chunks_jsonl(chunks_path)
    return _build_corpus_report(
        documents,
        chunks,
        top_limit=top_limit,
        emerging_limit=emerging_limit,
        orphan_limit=orphan_limit,
        orphan_threshold=orphan_threshold,
    )


def _build_corpus_report(
    documents: list[Document],
    chunks: list[Chunk],
    *,
    top_limit: int,
    emerging_limit: int,
    orphan_limit: int,
    orphan_threshold: float,
) -> CorpusReport:
    motif_candidates = _extract_motif_candidates(documents, chunks)
    top_motifs = _top_motifs(motif_candidates, limit=top_limit)
    top_texts = {motif.text for motif in top_motifs}
    emerging_motifs = _emerging_motifs(
        motif_candidates,
        excluded_texts=top_texts,
        limit=emerging_limit,
    )
    orphan_notes = _find_orphan_notes(
        documents,
        threshold=orphan_threshold,
        limit=orphan_limit,
    )
    return CorpusReport(
        top_motifs=top_motifs,
        emerging_motifs=emerging_motifs,
        orphan_notes=orphan_notes,
    )


def _extract_motif_candidates(
    documents: list[Document],
    chunks: list[Chunk],
) -> list[MotifCandidate]:
    text_units = [chunk.text for chunk in chunks] or [
        document.text for document in documents
    ]
    occurrence_counts: Counter[str] = Counter()

    for text in text_units:
        tokens = _tokenize(text)
        occurrence_counts.update(tokens)
        occurrence_counts.update(_bigrams(tokens))

    document_counts: Counter[str] = Counter()
    for document in documents:
        tokens = _tokenize(document.text)
        document_counts.update(set(tokens))
        document_counts.update(set(_bigrams(tokens)))

    candidates = [
        MotifCandidate(
            text=text,
            occurrences=occurrences,
            document_count=document_counts.get(text, 0),
        )
        for text, occurrences in occurrence_counts.items()
        if occurrences > 1 and _is_useful_motif(text)
    ]
    candidates.sort(
        key=lambda motif: (-motif.occurrences, -motif.document_count, motif.text)
    )
    return candidates


def _top_motifs(
    candidates: list[MotifCandidate],
    *,
    limit: int,
) -> list[MotifCandidate]:
    return [
        motif
        for motif in candidates
        if motif.document_count > 1
    ][:limit]


def _emerging_motifs(
    candidates: list[MotifCandidate],
    *,
    excluded_texts: set[str],
    limit: int,
) -> list[MotifCandidate]:
    emerging = [
        motif
        for motif in candidates
        if motif.text not in excluded_texts and motif.occurrences <= 4
    ]
    emerging.sort(
        key=lambda motif: (motif.occurrences, -motif.document_count, motif.text)
    )
    return emerging[:limit]


def _find_orphan_notes(
    documents: list[Document],
    *,
    threshold: float,
    limit: int,
) -> list[OrphanNote]:
    token_sets = [
        (document, set(_tokenize(document.text)))
        for document in documents
    ]
    orphan_notes: list[OrphanNote] = []

    for document, tokens in token_sets:
        best_overlap = 0.0
        for other_document, other_tokens in token_sets:
            if other_document.id == document.id:
                continue
            best_overlap = max(
                best_overlap,
                _jaccard_similarity(tokens, other_tokens),
            )

        if best_overlap <= threshold:
            orphan_notes.append(
                OrphanNote(
                    title=document.title,
                    relative_path=document.metadata.relative_path,
                    best_overlap=best_overlap,
                )
            )

    orphan_notes.sort(key=lambda note: (note.best_overlap, note.relative_path))
    return orphan_notes[:limit]


def _tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[a-zа-яё][a-zа-яё0-9-]{2,}", text.lower())
    return [
        token
        for token in raw_tokens
        if token not in STOPWORDS and len(token) >= 3
    ]


def _bigrams(tokens: list[str]) -> list[str]:
    return [
        f"{left} {right}"
        for left, right in zip(tokens, tokens[1:])
        if left != right
    ]


def _is_useful_motif(text: str) -> bool:
    return len(text) >= 3 and not text.isdigit()


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)

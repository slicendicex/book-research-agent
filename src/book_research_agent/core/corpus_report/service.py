from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pymorphy3

from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk
from book_research_agent.core.corpus_report.models import (
    ConceptCandidate,
    ConceptCoOccurrence,
    CorpusReport,
    OrphanNote,
)
from book_research_agent.core.config.settings import DATA_DIR
from book_research_agent.core.documents.models import Document
from book_research_agent.core.ingestion.serialize import read_documents_jsonl


DEFAULT_CONCEPT_STOPLIST_PATH = DATA_DIR / "config" / "concept_stoplist.txt"

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
    "где",
    "даже",
    "для",
    "другая",
    "другие",
    "другой",
    "должен",
    "должна",
    "должно",
    "должны",
    "есть",
    "еще",
    "ещё",
    "если",
    "или",
    "именно",
    "как",
    "когда",
    "каждая",
    "каждое",
    "каждый",
    "которая",
    "которое",
    "которые",
    "которого",
    "котором",
    "который",
    "которой",
    "которым",
    "которых",
    "которую",
    "может",
    "него",
    "нет",
    "нужно",
    "один",
    "одна",
    "одно",
    "одного",
    "она",
    "они",
    "перед",
    "под",
    "после",
    "поэтому",
    "потому",
    "почему",
    "просто",
    "себя",
    "свои",
    "своё",
    "свое",
    "своей",
    "свой",
    "свою",
    "так",
    "там",
    "те",
    "тех",
    "то",
    "тогда",
    "тот",
    "только",
    "твоё",
    "твое",
    "твой",
    "твоя",
    "уже",
    "что",
    "чтобы",
    "через",
    "этого",
    "этот",
    "это",
}

LOW_SIGNAL_CONCEPTS = {
    "КОТОР",
    "ПОД",
    "ПОЧЕМ",
    "ПОЭТОМ",
    "СИСТЕМ",
    "СИСТЕМА",
    "ДОЛЖН",
    "ДРУГ",
    "ПРАВО",
}

CONCEPT_ALIASES = {
    "auditor": "AUDITOR",
    "museum": "MUSEUM",
    "old": "OLD MAN",
    "аудитор": "АУДИТОР",
    "аудитора": "АУДИТОР",
    "аудитором": "АУДИТОР",
    "аудитору": "АУДИТОР",
    "аудиторы": "АУДИТОР",
    "дерево": "ДЕРЕВО",
    "дерева": "ДЕРЕВО",
    "деревом": "ДЕРЕВО",
    "дереву": "ДЕРЕВО",
    "лес": "ЛЕС",
    "леса": "ЛЕС",
    "лесом": "ЛЕС",
    "лесу": "ЛЕС",
    "музеем": "МУЗЕЙ",
    "музей": "МУЗЕЙ",
    "музея": "МУЗЕЙ",
    "музею": "МУЗЕЙ",
    "память": "ПАМЯТЬ",
    "памяти": "ПАМЯТЬ",
    "ритуал": "РИТУАЛ",
    "ритуала": "РИТУАЛ",
    "ритуалом": "РИТУАЛ",
    "старик": "СТАРИК",
    "старика": "СТАРИК",
    "стариком": "СТАРИК",
    "старику": "СТАРИК",
    "система": "СИСТЕМА",
    "системе": "СИСТЕМА",
    "системой": "СИСТЕМА",
    "систему": "СИСТЕМА",
    "системы": "СИСТЕМА",
    "стол": "СТОЛ",
    "стола": "СТОЛ",
    "столом": "СТОЛ",
    "столу": "СТОЛ",
    "трещина": "ТРЕЩИНА",
    "трещине": "ТРЕЩИНА",
    "трещиной": "ТРЕЩИНА",
    "трещину": "ТРЕЩИНА",
    "трещины": "ТРЕЩИНА",
    "форма": "ФОРМА",
    "форме": "ФОРМА",
    "формой": "ФОРМА",
    "форму": "ФОРМА",
    "формы": "ФОРМА",
    "читатель": "ЧИТАТЕЛЬ",
    "читателя": "ЧИТАТЕЛЬ",
    "читателем": "ЧИТАТЕЛЬ",
    "читателю": "ЧИТАТЕЛЬ",
    "жизнь": "ЖИЗНЬ",
    "жизни": "ЖИЗНЬ",
    "жизнью": "ЖИЗНЬ",
}

ALLOWED_RUSSIAN_POS = {"NOUN"}


def build_corpus_report(
    documents_path: Path,
    chunks_path: Path,
    *,
    concept_stoplist_path: Path | None = None,
    top_limit: int = 10,
    emerging_limit: int = 10,
    orphan_limit: int = 10,
    orphan_threshold: float = 0.08,
) -> CorpusReport:
    documents = read_documents_jsonl(documents_path)
    chunks = read_chunks_jsonl(chunks_path)
    stoplist_concepts = _load_concept_stoplist(
        concept_stoplist_path or DEFAULT_CONCEPT_STOPLIST_PATH
    )
    return _build_corpus_report(
        documents,
        chunks,
        stoplist_concepts=stoplist_concepts,
        top_limit=top_limit,
        emerging_limit=emerging_limit,
        orphan_limit=orphan_limit,
        orphan_threshold=orphan_threshold,
    )


def _build_corpus_report(
    documents: list[Document],
    chunks: list[Chunk],
    *,
    stoplist_concepts: set[str],
    top_limit: int,
    emerging_limit: int,
    orphan_limit: int,
    orphan_threshold: float,
) -> CorpusReport:
    concept_candidates = _extract_concept_candidates(
        documents,
        chunks,
        stoplist_concepts=stoplist_concepts,
    )
    core_concepts = _core_concepts(concept_candidates, limit=top_limit)
    core_texts = {concept.text for concept in core_concepts}
    secondary_concepts = _secondary_concepts(
        concept_candidates,
        excluded_texts=core_texts,
        limit=emerging_limit,
    )
    co_occurrences = _strong_co_occurrences(
        documents,
        stoplist_concepts=stoplist_concepts,
        limit=top_limit,
    )
    orphan_notes = _find_orphan_notes(
        documents,
        stoplist_concepts=stoplist_concepts,
        threshold=orphan_threshold,
        limit=orphan_limit,
    )
    return CorpusReport(
        core_concepts=core_concepts,
        secondary_concepts=secondary_concepts,
        co_occurrences=co_occurrences,
        orphan_notes=orphan_notes,
    )


def _extract_concept_candidates(
    documents: list[Document],
    chunks: list[Chunk],
    *,
    stoplist_concepts: set[str],
) -> list[ConceptCandidate]:
    text_units = [chunk.text for chunk in chunks] or [
        document.text for document in documents
    ]
    occurrence_counts: Counter[str] = Counter()

    for text in text_units:
        occurrence_counts.update(
            _concepts_from_text(text, stoplist_concepts=stoplist_concepts)
        )

    document_counts: Counter[str] = Counter()
    for document in documents:
        document_counts.update(
            set(_concepts_from_text(document.text, stoplist_concepts=stoplist_concepts))
        )

    candidates = [
        ConceptCandidate(
            text=text,
            occurrences=occurrences,
            document_count=document_counts.get(text, 0),
        )
        for text, occurrences in occurrence_counts.items()
        if occurrences > 1 and _is_useful_concept(text)
    ]
    candidates.sort(key=_concept_sort_key)
    return candidates


def _core_concepts(
    candidates: list[ConceptCandidate],
    *,
    limit: int,
) -> list[ConceptCandidate]:
    return [
        concept
        for concept in candidates
        if concept.document_count > 1
    ][:limit]


def _secondary_concepts(
    candidates: list[ConceptCandidate],
    *,
    excluded_texts: set[str],
    limit: int,
) -> list[ConceptCandidate]:
    secondary = [
        concept
        for concept in candidates
        if concept.text not in excluded_texts and concept.document_count > 1
    ]
    secondary.sort(key=_concept_sort_key)
    return secondary[:limit]


def _strong_co_occurrences(
    documents: list[Document],
    *,
    stoplist_concepts: set[str],
    limit: int,
) -> list[ConceptCoOccurrence]:
    pair_counts: Counter[tuple[str, str]] = Counter()

    for document in documents:
        concepts = sorted(
            set(_concepts_from_text(document.text, stoplist_concepts=stoplist_concepts))
        )
        for index, left in enumerate(concepts):
            for right in concepts[index + 1:]:
                pair_counts[(left, right)] += 1

    pairs = [
        ConceptCoOccurrence(
            left=left,
            right=right,
            document_count=document_count,
        )
        for (left, right), document_count in pair_counts.items()
        if document_count > 1
    ]
    pairs.sort(key=lambda pair: (-pair.document_count, pair.left, pair.right))
    return pairs[:limit]


def _find_orphan_notes(
    documents: list[Document],
    *,
    stoplist_concepts: set[str],
    threshold: float,
    limit: int,
) -> list[OrphanNote]:
    token_sets = [
        (
            document,
            set(_concepts_from_text(document.text, stoplist_concepts=stoplist_concepts)),
        )
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


def _concepts_from_text(text: str, *, stoplist_concepts: set[str]) -> list[str]:
    concepts = [
        concept
        for token in _tokenize(text)
        if (concept := _normalize_concept(token)) is not None
        and concept not in stoplist_concepts
    ]
    return concepts


def _load_concept_stoplist(path: Path) -> set[str]:
    if not path.exists():
        return set()

    stoplist_concepts: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", maxsplit=1)[0].strip()
        if not entry:
            continue
        concept = _normalize_concept(entry)
        if concept is not None:
            stoplist_concepts.add(concept)
    return stoplist_concepts


def _normalize_concept(token: str) -> str | None:
    token = token.lower()
    concept = CONCEPT_ALIASES.get(token)
    if concept is None and _is_russian_token(token):
        parsed = _morph_analyzer().parse(token)[0]
        if parsed.tag.POS not in ALLOWED_RUSSIAN_POS:
            return None
        concept = CONCEPT_ALIASES.get(parsed.normal_form, parsed.normal_form.upper())
    elif concept is None:
        concept = token.upper()

    if concept in LOW_SIGNAL_CONCEPTS or len(concept) < 3:
        return None
    return concept


def _is_russian_token(token: str) -> bool:
    return bool(re.search(r"[а-яё]", token))


@lru_cache(maxsize=1)
def _morph_analyzer() -> pymorphy3.MorphAnalyzer:
    return pymorphy3.MorphAnalyzer()


def _is_useful_concept(text: str) -> bool:
    return len(text) >= 3 and not text.isdigit()


def _concept_sort_key(concept: ConceptCandidate) -> tuple[int, int, str]:
    return (-concept.document_count, -concept.occurrences, concept.text)


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)

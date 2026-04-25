import argparse
import json
import sys
from pathlib import Path

from book_research_agent.core.answering import (
    DEFAULT_ANSWER_TOP_K,
    DEFAULT_CANON_TOP_K,
    DEFAULT_COMPARE_TOP_K,
    DEFAULT_CONTRADICT_TOP_K,
    answer_query,
    canon_query,
    compare_queries,
    contradict_queries,
)
from book_research_agent.core.chunking import chunk_documents, write_chunks_jsonl
from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.config.env import get_env_var_status, load_project_env
from book_research_agent.core.config.settings import load_settings
from book_research_agent.core.corpus_report import (
    ConceptCandidate,
    ConceptCoOccurrence,
    CorpusReport,
    OrphanNote,
    build_corpus_report,
)
from book_research_agent.core.diagnostics import (
    DiagnosticLookupError,
    get_chunk_by_id,
    get_corpus_stats,
    get_document_by_path,
    get_indexed_chunk_by_id,
)
from book_research_agent.core.evaluation import (
    build_default_eval_run_path,
    build_eval_run_diff,
    get_latest_eval_run_paths,
    prune_auto_saved_eval_runs,
    read_eval_cases_jsonl,
    read_eval_report_json,
    resolve_eval_run_path,
    run_eval_cases,
    summarize_eval_results,
    write_eval_diff_json,
    write_eval_report_json,
)
from book_research_agent.core.hygiene import (
    DuplicateGroup,
    find_duplicate_chunks,
    find_duplicate_documents,
    get_dedup_stats,
)
from book_research_agent.core.ingestion import ingest_documents, write_documents_jsonl
from book_research_agent.core.ingestion.serialize import read_documents_jsonl
from book_research_agent.core.indexing import build_chunk_index, read_indexed_chunks_jsonl
from book_research_agent.core.indexing.serialize import write_indexed_chunks_jsonl
from book_research_agent.core.providers.factory import (
    create_embedding_provider,
    create_generation_provider,
)
from book_research_agent.core.retrieval import (
    build_source_results,
    retrieve_reranked_results,
    search_index,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="book-research-agent",
        description="Minimal CLI scaffold for the book research agent project.",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Print a safe runtime configuration summary.",
    )
    doctor_parser.set_defaults(handler=run_doctor)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest local .txt and .md files into documents.jsonl.",
    )
    ingest_parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Source directory to scan. Defaults to data/raw.",
    )
    ingest_parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output JSONL file path. Defaults to data/processed/documents.jsonl.",
    )
    ingest_parser.set_defaults(handler=run_ingest)

    chunk_parser = subparsers.add_parser(
        "chunk",
        help="Chunk normalized documents from documents.jsonl into chunks.jsonl.",
    )
    chunk_parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    chunk_parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    chunk_parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Maximum characters per chunk.",
    )
    chunk_parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=120,
        help="Character overlap between adjacent chunks.",
    )
    chunk_parser.set_defaults(handler=run_chunk)

    index_parser = subparsers.add_parser(
        "index",
        help="Embed chunks and write a local file-based chunk index.",
    )
    index_parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    index_parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Output index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    index_parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Number of chunk texts to embed per batch.",
    )
    index_parser.set_defaults(handler=run_index)

    search_parser = subparsers.add_parser(
        "search",
        help="Search the local chunk index with cosine similarity.",
    )
    search_parser.add_argument("query", help="Search query text.")
    search_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of matches to return.",
    )
    search_parser.set_defaults(handler=run_search)

    source_parser = subparsers.add_parser(
        "source",
        help="Search the local chunk index in a more source-facing display mode.",
    )
    source_parser.add_argument("query", help="Search query text.")
    source_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    source_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum number of source-facing matches to return.",
    )
    source_parser.add_argument(
        "--excerpt-length",
        type=int,
        default=160,
        help="Maximum display length for formatted excerpts.",
    )
    source_parser.set_defaults(handler=run_source)

    answer_parser = subparsers.add_parser(
        "answer",
        help="Answer a question using retrieval-first grounded generation.",
    )
    answer_parser.add_argument("query", help="Question to answer.")
    answer_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    answer_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_ANSWER_TOP_K,
        help="Maximum number of grounded source references to use.",
    )
    answer_parser.set_defaults(handler=run_answer)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two queries using retrieval-first grounded generation.",
    )
    compare_parser.add_argument("left_query", help="First query to compare.")
    compare_parser.add_argument("right_query", help="Second query to compare.")
    compare_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    compare_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_COMPARE_TOP_K,
        help="Maximum number of source references to use per side.",
    )
    compare_parser.set_defaults(handler=run_compare)

    contradict_parser = subparsers.add_parser(
        "contradict",
        help="Judge tension or contradiction between two retrieval-grounded queries.",
    )
    contradict_parser.add_argument("left_query", help="First claim or query.")
    contradict_parser.add_argument("right_query", help="Second claim or query.")
    contradict_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    contradict_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_CONTRADICT_TOP_K,
        help="Maximum number of source references to use per side.",
    )
    contradict_parser.set_defaults(handler=run_contradict)

    canon_parser = subparsers.add_parser(
        "canon",
        help="Produce a short source-grounded canon-oriented judgment.",
    )
    canon_parser.add_argument("query", help="Canon query to judge.")
    canon_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    canon_parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_CANON_TOP_K,
        help="Maximum number of grounded source references to use.",
    )
    canon_parser.set_defaults(handler=run_canon)

    eval_parser = subparsers.add_parser(
        "eval",
        help="Run minimal grounded health-check eval cases.",
    )
    eval_parser.add_argument(
        "--cases-file",
        type=Path,
        default=None,
        help="Input eval cases JSONL path. Defaults to data/eval/eval_cases.jsonl.",
    )
    eval_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    eval_parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Maximum number of source references to use per eval query.",
    )
    eval_parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output path for a structured eval report.",
    )
    eval_parser.set_defaults(handler=run_eval)

    eval_compare_parser = subparsers.add_parser(
        "eval-compare",
        help="Compare two saved eval run files.",
    )
    eval_compare_parser.add_argument(
        "run_a",
        nargs="?",
        help="First eval run file. Short names resolve inside data/eval/runs/.",
    )
    eval_compare_parser.add_argument(
        "run_b",
        nargs="?",
        help="Second eval run file. Short names resolve inside data/eval/runs/.",
    )
    eval_compare_parser.add_argument(
        "--latest",
        action="store_true",
        help="Compare the two newest saved eval run files in data/eval/runs/.",
    )
    eval_compare_parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional JSON output path for a structured diff report.",
    )
    eval_compare_parser.set_defaults(handler=run_eval_compare)

    stats_parser = subparsers.add_parser(
        "stats",
        help="Inspect basic corpus artifact counts.",
    )
    stats_parser.add_argument(
        "--documents-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    stats_parser.add_argument(
        "--chunks-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    stats_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    stats_parser.set_defaults(handler=run_stats)

    dedup_stats_parser = subparsers.add_parser(
        "dedup-stats",
        help="Inspect likely duplicate document and chunk group counts.",
    )
    dedup_stats_parser.add_argument(
        "--documents-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    dedup_stats_parser.add_argument(
        "--chunks-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    dedup_stats_parser.set_defaults(handler=run_dedup_stats)

    find_duplicates_parser = subparsers.add_parser(
        "find-duplicates",
        help="Find likely duplicate or near-duplicate processed documents.",
    )
    find_duplicates_parser.add_argument(
        "--documents-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    find_duplicates_parser.set_defaults(handler=run_find_duplicates)

    find_duplicate_chunks_parser = subparsers.add_parser(
        "find-duplicate-chunks",
        help="Find likely duplicate or near-duplicate processed chunks.",
    )
    find_duplicate_chunks_parser.add_argument(
        "--chunks-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    find_duplicate_chunks_parser.set_defaults(handler=run_find_duplicate_chunks)

    corpus_report_parser = subparsers.add_parser(
        "corpus-report",
        help="Surface concept-level corpus coverage and possible orphan notes.",
    )
    corpus_report_parser.add_argument(
        "--documents-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    corpus_report_parser.add_argument(
        "--chunks-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    corpus_report_parser.add_argument(
        "--top-limit",
        type=int,
        default=10,
        help="Maximum number of top motifs to show.",
    )
    corpus_report_parser.add_argument(
        "--emerging-limit",
        type=int,
        default=10,
        help="Maximum number of emerging motifs to show.",
    )
    corpus_report_parser.add_argument(
        "--orphan-limit",
        type=int,
        default=10,
        help="Maximum number of potential orphan notes to show.",
    )
    corpus_report_parser.set_defaults(handler=run_corpus_report)

    inspect_doc_parser = subparsers.add_parser(
        "inspect-doc",
        help="Inspect a processed document by relative path.",
    )
    inspect_doc_parser.add_argument(
        "--path",
        required=True,
        help="Document relative path inside documents.jsonl.",
    )
    inspect_doc_parser.add_argument(
        "--documents-file",
        type=Path,
        default=None,
        help="Input documents JSONL path. Defaults to data/processed/documents.jsonl.",
    )
    inspect_doc_parser.set_defaults(handler=run_inspect_doc)

    inspect_chunk_parser = subparsers.add_parser(
        "inspect-chunk",
        help="Inspect a chunk by chunk id.",
    )
    inspect_chunk_parser.add_argument(
        "--chunk-id",
        required=True,
        help="Chunk id to inspect.",
    )
    inspect_chunk_parser.add_argument(
        "--chunks-file",
        type=Path,
        default=None,
        help="Input chunks JSONL path. Defaults to data/processed/chunks.jsonl.",
    )
    inspect_chunk_parser.set_defaults(handler=run_inspect_chunk)

    inspect_index_parser = subparsers.add_parser(
        "inspect-index",
        help="Inspect an indexed chunk by chunk id.",
    )
    inspect_index_parser.add_argument(
        "--chunk-id",
        required=True,
        help="Indexed chunk id to inspect.",
    )
    inspect_index_parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Input index JSONL path. Defaults to data/index/chunk_index.jsonl.",
    )
    inspect_index_parser.set_defaults(handler=run_inspect_index)

    return parser


def run_doctor(_args: argparse.Namespace) -> int:
    settings = load_settings()

    print("book-research-agent doctor")
    print(f"environment: {settings.environment}")
    print(f"project_root: {settings.project_root}")
    print(f"data_raw_dir: {settings.data_raw_dir}")
    print(f"data_processed_dir: {settings.data_processed_dir}")
    print(f"data_index_dir: {settings.data_index_dir}")
    print(
        "embedding_provider: "
        f"{settings.embedding_provider} ({settings.embedding_model})"
    )
    print(
        "generation_provider: "
        f"{settings.generation_provider} ({settings.generation_model})"
    )
    _print_env_var_status("cohere_api_key", "COHERE_API_KEY")
    _print_env_var_status("openai_api_key", "OPENAI_API_KEY")
    print(
        "gemini_api_key_present: "
        f"{'yes' if settings.has_gemini_api_key else 'no'}"
    )
    _print_env_var_status("anthropic_api_key", "ANTHROPIC_API_KEY")
    return 0


def _print_env_var_status(label: str, env_var_name: str) -> None:
    status = get_env_var_status(env_var_name)
    print(f"{label}_present: {'yes' if status.present else 'no'}")
    print(f"{label}_source: {status.source}")


def run_ingest(args: argparse.Namespace) -> int:
    settings = load_settings()
    input_dir = args.input_dir or settings.data_raw_dir
    output_file = args.output_file or (settings.data_processed_dir / "documents.jsonl")

    result = ingest_documents(input_dir)
    write_documents_jsonl(result.documents, output_file)

    print("book-research-agent ingest")
    print(f"scanned_files: {result.scanned_files}")
    print(f"supported_files: {result.supported_files}")
    print(f"skipped_files: {result.skipped_files}")
    print(f"produced_documents: {result.produced_documents}")
    print(f"output_path: {output_file}")
    return 0


def run_chunk(args: argparse.Namespace) -> int:
    settings = load_settings()
    input_file = args.input_file or (settings.data_processed_dir / "documents.jsonl")
    output_file = args.output_file or (settings.data_processed_dir / "chunks.jsonl")

    documents = read_documents_jsonl(input_file)
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    write_chunks_jsonl(chunks, output_file)

    print("book-research-agent chunk")
    print(f"input_documents: {len(documents)}")
    print(f"produced_chunks: {len(chunks)}")
    print(f"chunk_size: {args.chunk_size}")
    print(f"chunk_overlap: {args.chunk_overlap}")
    print(f"output_path: {output_file}")
    return 0


def run_index(args: argparse.Namespace) -> int:
    settings = load_settings()
    input_file = args.input_file or (settings.data_processed_dir / "chunks.jsonl")
    output_file = args.output_file or (settings.data_index_dir / "chunk_index.jsonl")

    chunks = read_chunks_jsonl(input_file)
    embedding_provider = create_embedding_provider(settings)
    indexed_chunks = build_chunk_index(
        chunks,
        embedding_provider=embedding_provider,
        embedding_model=settings.embedding_model,
        batch_size=args.batch_size,
    )
    write_indexed_chunks_jsonl(indexed_chunks, output_file)

    print("book-research-agent index")
    print(f"input_chunks: {len(chunks)}")
    print(f"indexed_chunks: {len(indexed_chunks)}")
    print(f"embedding_provider: {embedding_provider.provider_name}")
    print(f"embedding_model: {settings.embedding_model}")
    print(f"output_path: {output_file}")
    return 0


def run_search(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    results = search_index(
        query=args.query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=args.top_k,
    )

    print("book-research-agent search")
    print(f"query: {args.query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print(f"matches: {len(results)}")

    for result in results:
        excerpt = result.indexed_chunk.text.replace("\n", " ").strip()
        excerpt = excerpt[:160]
        print("---")
        print(f"score: {result.score:.4f}")
        print(f"title: {result.indexed_chunk.metadata.source_title}")
        print(f"path: {result.indexed_chunk.metadata.document_relative_path}")
        print(f"chunk_index: {result.indexed_chunk.metadata.chunk_index}")
        print(f"excerpt: {excerpt}")

    return 0


def run_source(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    search_results = retrieve_reranked_results(
        query=args.query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )
    source_results = build_source_results(
        search_results,
        max_results=args.top_k,
        excerpt_length=args.excerpt_length,
        neighbor_window=0,
    )

    print("book-research-agent source")
    print(f"query: {args.query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print(f"matches: {len(source_results)}")

    for result in source_results:
        print("---")
        print(f"score: {result.score:.4f}")
        print(f"title: {result.title}")
        print(f"path: {result.relative_path}")
        print(f"chunk_index: {result.chunk_index}")
        print(f"excerpt: {result.excerpt}")

    return 0


def run_answer(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    result = answer_query(
        query=args.query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )

    print("book-research-agent answer")
    print(f"query: {result.query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print("answer:")
    print(result.answer)
    print("sources_used:")

    for source in result.sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    return 0


def run_compare(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    result = compare_queries(
        left_query=args.left_query,
        right_query=args.right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )

    print("book-research-agent compare")
    print(f"left_query: {result.left_query}")
    print(f"right_query: {result.right_query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print("comparison:")
    print(result.comparison)
    print("left_sources_used:")

    for source in result.left_sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    print("right_sources_used:")

    for source in result.right_sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    return 0


def run_contradict(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    result = contradict_queries(
        left_query=args.left_query,
        right_query=args.right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )

    print("book-research-agent contradict")
    print(f"left_query: {result.left_query}")
    print(f"right_query: {result.right_query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print("judgment:")
    print(result.judgment)
    print("left_sources_used:")

    for source in result.left_sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    print("right_sources_used:")

    for source in result.right_sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    return 0


def run_canon(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    result = canon_query(
        query=args.query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )

    print("book-research-agent canon")
    print(f"query: {result.query}")
    print(f"top_k: {args.top_k}")
    print(f"index_path: {index_file}")
    print("judgment:")
    print(result.judgment)
    print("sources_used:")

    for source in result.sources_used:
        print("---")
        print(f"title: {source.title}")
        print(f"path: {source.relative_path}")
        print(f"chunk_index: {source.chunk_index}")

    return 0


def run_eval(args: argparse.Namespace) -> int:
    settings = load_settings()
    cases_file = args.cases_file or (settings.data_dir / "eval" / "eval_cases.jsonl")
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")
    runs_dir = settings.data_dir / "eval" / "runs"

    cases = read_eval_cases_jsonl(cases_file)
    indexed_chunks = read_indexed_chunks_jsonl(index_file)
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)
    results = run_eval_cases(
        cases,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=args.top_k,
    )
    summary = summarize_eval_results(results)

    print("book-research-agent eval")
    print(f"cases_path: {cases_file}")
    print(f"index_path: {index_file}")
    print(f"cases: {len(cases)}")

    for result in results:
        suffix = f" ({result.message})" if result.message else ""
        print(f"[{result.case_id}] {result.status}{suffix}")
        print(f"mode: {result.mode}")
        print(f"retrieval_count: {result.retrieval_count}")
        print(f"answer_present: {'yes' if result.answer_present else 'no'}")
        for snapshot in result.retrieval_snapshots:
            print(f"query: {snapshot.query}")
            print(f"top_paths: {snapshot.top_paths}")
            print(f"top_chunk_ids: {snapshot.top_chunk_ids}")
            print(f"top_scores: {snapshot.top_scores}")
            print(f"unique_document_count: {snapshot.unique_document_count}")
            print(f"top_path_repeat_count: {snapshot.top_path_repeat_count}")
            print(f"duplicate_like_count: {snapshot.duplicate_like_count}")
            print(f"score_spread: {snapshot.score_spread:.4f}")

    print("Summary:")
    print(f"PASS: {summary.pass_count}")
    print(f"WARN: {summary.warn_count}")
    print(f"FAIL: {summary.fail_count}")
    output_path = args.json_out
    auto_saved = output_path is None
    if output_path is None:
        output_path = build_default_eval_run_path(runs_dir)
    write_eval_report_json(
        output_path,
        results=results,
        summary=summary,
    )
    print(f"saved_run: {output_path}")
    if auto_saved:
        prune_auto_saved_eval_runs(runs_dir)
    return 1 if summary.fail_count else 0


def run_eval_compare(args: argparse.Namespace) -> int:
    settings = load_settings()
    runs_dir = settings.data_dir / "eval" / "runs"

    if args.latest:
        if args.run_a is not None or args.run_b is not None:
            print("--latest does not accept run file arguments", file=sys.stderr)
            return 1
        try:
            run_a_path, run_b_path = get_latest_eval_run_paths(runs_dir)
        except (FileNotFoundError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
    else:
        if args.run_a is None or args.run_b is None:
            print("eval-compare requires two run files or --latest", file=sys.stderr)
            return 1
        try:
            run_a_path = resolve_eval_run_path(args.run_a, runs_dir=runs_dir)
            run_b_path = resolve_eval_run_path(args.run_b, runs_dir=runs_dir)
        except FileNotFoundError as error:
            print(str(error), file=sys.stderr)
            return 1

    try:
        before_report = read_eval_report_json(run_a_path)
        after_report = read_eval_report_json(run_b_path)
    except (FileNotFoundError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    diff = build_eval_run_diff(
        before_report,
        after_report,
        before_path=run_a_path,
        after_path=run_b_path,
    )

    print("book-research-agent eval-compare")
    print(f"before_run: {run_a_path}")
    print(f"after_run: {run_b_path}")
    print("summary_delta:")
    print(f"PASS: {diff.pass_delta:+d}")
    print(f"WARN: {diff.warn_delta:+d}")
    print(f"FAIL: {diff.fail_delta:+d}")
    print(f"changed_cases: {len(diff.changed_cases)}")

    for case_diff in diff.changed_cases:
        print("---")
        print(f"case_id: {case_diff.case_id}")
        print(f"mode: {case_diff.mode}")
        if case_diff.status_before != case_diff.status_after:
            print(f"status: {case_diff.status_before} -> {case_diff.status_after}")
        if case_diff.retrieval_count_before != case_diff.retrieval_count_after:
            print(
                "retrieval_count: "
                f"{case_diff.retrieval_count_before} -> {case_diff.retrieval_count_after}"
            )
        if case_diff.top_paths_before != case_diff.top_paths_after:
            print(f"top_paths_before: {case_diff.top_paths_before}")
            print(f"top_paths_after: {case_diff.top_paths_after}")
        if case_diff.top_scores_before != case_diff.top_scores_after:
            print(f"top_scores_before: {case_diff.top_scores_before}")
            print(f"top_scores_after: {case_diff.top_scores_after}")
        if (
            case_diff.unique_document_count_before
            != case_diff.unique_document_count_after
        ):
            print(
                "unique_document_count: "
                f"{case_diff.unique_document_count_before} -> "
                f"{case_diff.unique_document_count_after}"
            )
        if (
            case_diff.duplicate_like_count_before
            != case_diff.duplicate_like_count_after
        ):
            print(
                "duplicate_like_count: "
                f"{case_diff.duplicate_like_count_before} -> "
                f"{case_diff.duplicate_like_count_after}"
            )

    if args.json_out is not None:
        write_eval_diff_json(args.json_out, diff=diff)
        print(f"saved_diff: {args.json_out}")

    return 0


def run_stats(args: argparse.Namespace) -> int:
    settings = load_settings()
    documents_file = (
        args.documents_file or (settings.data_processed_dir / "documents.jsonl")
    )
    chunks_file = args.chunks_file or (settings.data_processed_dir / "chunks.jsonl")
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    try:
        stats = get_corpus_stats(documents_file, chunks_file, index_file)
    except (DiagnosticLookupError, FileNotFoundError) as error:
        return _print_diagnostic_error(error)

    print("book-research-agent stats")
    print(f"documents_path: {stats.documents_path}")
    print(f"documents: {stats.document_count}")
    print(f"chunks_path: {stats.chunks_path}")
    print(f"chunks: {stats.chunk_count}")
    print(f"index_path: {stats.index_path}")
    print(f"indexed_chunks: {stats.indexed_chunk_count}")
    return 0


def run_dedup_stats(args: argparse.Namespace) -> int:
    settings = load_settings()
    documents_file = (
        args.documents_file or (settings.data_processed_dir / "documents.jsonl")
    )
    chunks_file = args.chunks_file or (settings.data_processed_dir / "chunks.jsonl")

    try:
        stats = get_dedup_stats(documents_file, chunks_file)
    except FileNotFoundError as error:
        return _print_diagnostic_error(error)

    print("book-research-agent dedup-stats")
    print(f"documents_path: {documents_file}")
    print(f"documents: {stats.document_count}")
    print(f"chunks_path: {chunks_file}")
    print(f"chunks: {stats.chunk_count}")
    print(f"duplicate_document_groups: {stats.duplicate_document_group_count}")
    print(f"duplicate_chunk_groups: {stats.duplicate_chunk_group_count}")
    return 0


def run_find_duplicates(args: argparse.Namespace) -> int:
    settings = load_settings()
    documents_file = (
        args.documents_file or (settings.data_processed_dir / "documents.jsonl")
    )

    try:
        groups = find_duplicate_documents(documents_file)
    except FileNotFoundError as error:
        return _print_diagnostic_error(error)

    print("book-research-agent find-duplicates")
    print(f"documents_path: {documents_file}")
    _print_duplicate_groups(groups, item_kind="document")
    return 0


def run_find_duplicate_chunks(args: argparse.Namespace) -> int:
    settings = load_settings()
    chunks_file = args.chunks_file or (settings.data_processed_dir / "chunks.jsonl")

    try:
        groups = find_duplicate_chunks(chunks_file)
    except FileNotFoundError as error:
        return _print_diagnostic_error(error)

    print("book-research-agent find-duplicate-chunks")
    print(f"chunks_path: {chunks_file}")
    _print_duplicate_groups(groups, item_kind="chunk")
    return 0


def run_corpus_report(args: argparse.Namespace) -> int:
    settings = load_settings()
    documents_file = (
        args.documents_file or (settings.data_processed_dir / "documents.jsonl")
    )
    chunks_file = args.chunks_file or (settings.data_processed_dir / "chunks.jsonl")

    report = build_corpus_report(
        documents_file,
        chunks_file,
        top_limit=args.top_limit,
        emerging_limit=args.emerging_limit,
        orphan_limit=args.orphan_limit,
    )

    print("book-research-agent corpus-report")
    print(f"documents_path: {documents_file}")
    print(f"chunks_path: {chunks_file}")
    _print_corpus_report(report)
    return 0


def _print_corpus_report(report: CorpusReport) -> None:
    print("Core concepts:")
    _print_concepts(report.core_concepts)
    print("Secondary concept lines:")
    _print_concepts(report.secondary_concepts)
    print("Strong co-occurrences:")
    _print_co_occurrences(report.co_occurrences)
    print("Potential orphan notes:")
    _print_orphan_notes(report.orphan_notes)


def _print_concepts(concepts: list[ConceptCandidate]) -> None:
    if not concepts:
        print("- none")
        return

    for concept in concepts:
        print(
            f"- {concept.text} "
            f"(occurrences: {concept.occurrences}, documents: {concept.document_count})"
        )


def _print_co_occurrences(pairs: list[ConceptCoOccurrence]) -> None:
    if not pairs:
        print("- none")
        return

    for pair in pairs:
        print(
            f"- {pair.left} <-> {pair.right} "
            f"(documents: {pair.document_count})"
        )


def _print_orphan_notes(orphan_notes: list[OrphanNote]) -> None:
    if not orphan_notes:
        print("- none")
        return

    for note in orphan_notes:
        print(
            f"- {note.title} | {note.relative_path} "
            f"(best_overlap: {note.best_overlap:.2f})"
        )


def run_inspect_doc(args: argparse.Namespace) -> int:
    settings = load_settings()
    documents_file = (
        args.documents_file or (settings.data_processed_dir / "documents.jsonl")
    )

    try:
        document = get_document_by_path(documents_file, args.path)
    except (DiagnosticLookupError, FileNotFoundError) as error:
        return _print_diagnostic_error(error)

    print("book-research-agent inspect-doc")
    print(f"documents_path: {documents_file}")
    print(f"id: {document.id}")
    print(f"title: {document.title}")
    print(f"path: {document.metadata.relative_path}")
    print(f"source_kind: {document.metadata.source_kind}")
    print(f"source_path: {document.metadata.source_path}")
    print(f"file_extension: {document.metadata.file_extension}")
    print(f"content_sha1: {document.metadata.content_sha1}")
    print(f"char_count: {document.char_count}")
    print("text:")
    print(document.text)
    return 0


def run_inspect_chunk(args: argparse.Namespace) -> int:
    settings = load_settings()
    chunks_file = args.chunks_file or (settings.data_processed_dir / "chunks.jsonl")

    try:
        chunk = get_chunk_by_id(chunks_file, args.chunk_id)
    except (DiagnosticLookupError, FileNotFoundError) as error:
        return _print_diagnostic_error(error)

    print("book-research-agent inspect-chunk")
    print(f"chunks_path: {chunks_file}")
    print(f"chunk_id: {chunk.id}")
    print(f"document_id: {chunk.document_id}")
    print(f"title: {chunk.metadata.source_title}")
    print(f"path: {chunk.metadata.document_relative_path}")
    print(f"chunk_index: {chunk.metadata.chunk_index}")
    print(f"char_start: {chunk.metadata.char_start}")
    print(f"char_end: {chunk.metadata.char_end}")
    print("text:")
    print(chunk.text)
    return 0


def run_inspect_index(args: argparse.Namespace) -> int:
    settings = load_settings()
    index_file = args.index_file or (settings.data_index_dir / "chunk_index.jsonl")

    try:
        indexed_chunk = get_indexed_chunk_by_id(index_file, args.chunk_id)
    except (DiagnosticLookupError, FileNotFoundError) as error:
        return _print_diagnostic_error(error)

    print("book-research-agent inspect-index")
    print(f"index_path: {index_file}")
    print(f"chunk_id: {indexed_chunk.chunk_id}")
    print(f"document_id: {indexed_chunk.document_id}")
    print(f"embedding_model: {indexed_chunk.embedding_model}")
    print(f"embedding_dimension: {len(indexed_chunk.embedding)}")
    print(f"title: {indexed_chunk.metadata.source_title}")
    print(f"path: {indexed_chunk.metadata.document_relative_path}")
    print(f"chunk_index: {indexed_chunk.metadata.chunk_index}")
    print(f"char_start: {indexed_chunk.metadata.char_start}")
    print(f"char_end: {indexed_chunk.metadata.char_end}")
    return 0


def _print_diagnostic_error(error: Exception) -> int:
    print(str(error), file=sys.stderr)
    return 1


def _print_duplicate_groups(groups: list[DuplicateGroup], *, item_kind: str) -> None:
    print(f"groups: {len(groups)}")

    for group_index, group in enumerate(groups, start=1):
        print("---")
        print(f"group: {group_index}")
        print(f"similarity: {group.similarity:.2f}")

        for item in group.items:
            print(f"{item_kind}_id: {item.item_id}")
            print(f"document_id: {item.document_id}")
            print(f"title: {item.title}")
            print(f"path: {item.relative_path}")
            if item.chunk_index is not None:
                print(f"chunk_index: {item.chunk_index}")


def main() -> int:
    load_project_env()
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "handler"):
        return args.handler(args)

    print("book-research-agent scaffold is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

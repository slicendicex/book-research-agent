import argparse
import sys
from pathlib import Path

from book_research_agent.core.answering import answer_query
from book_research_agent.core.chunking import chunk_documents, write_chunks_jsonl
from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.config.settings import load_settings
from book_research_agent.core.diagnostics import (
    DiagnosticLookupError,
    get_chunk_by_id,
    get_corpus_stats,
    get_document_by_path,
    get_indexed_chunk_by_id,
)
from book_research_agent.core.ingestion import ingest_documents, write_documents_jsonl
from book_research_agent.core.ingestion.serialize import read_documents_jsonl
from book_research_agent.core.indexing import build_chunk_index, read_indexed_chunks_jsonl
from book_research_agent.core.indexing.serialize import write_indexed_chunks_jsonl
from book_research_agent.core.providers.factory import (
    create_embedding_provider,
    create_generation_provider,
)
from book_research_agent.core.retrieval import build_source_results, search_index


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
        default=3,
        help="Maximum number of grounded source references to use.",
    )
    answer_parser.set_defaults(handler=run_answer)

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
    print(
        "cohere_api_key_present: "
        f"{'yes' if settings.has_cohere_api_key else 'no'}"
    )
    print(
        "openai_api_key_present: "
        f"{'yes' if settings.has_openai_api_key else 'no'}"
    )
    print(
        "gemini_api_key_present: "
        f"{'yes' if settings.has_gemini_api_key else 'no'}"
    )
    print(
        "anthropic_api_key_present: "
        f"{'yes' if settings.has_anthropic_api_key else 'no'}"
    )
    return 0


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
    candidate_count = max(args.top_k * 3, args.top_k)
    search_results = search_index(
        query=args.query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=candidate_count,
    )
    source_results = build_source_results(
        search_results,
        max_results=args.top_k,
        excerpt_length=args.excerpt_length,
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "handler"):
        return args.handler(args)

    print("book-research-agent scaffold is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

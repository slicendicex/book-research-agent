import argparse
from pathlib import Path

from book_research_agent.core.chunking import chunk_documents, write_chunks_jsonl
from book_research_agent.core.config.settings import load_settings
from book_research_agent.core.ingestion import ingest_documents, write_documents_jsonl
from book_research_agent.core.ingestion.serialize import read_documents_jsonl
from book_research_agent.core.providers.factory import (
    create_embedding_provider,
    create_generation_provider,
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

    return parser


def run_doctor(_args: argparse.Namespace) -> int:
    settings = load_settings()
    embedding_provider = create_embedding_provider(settings)
    generation_provider = create_generation_provider(settings)

    print("book-research-agent doctor")
    print(f"environment: {settings.environment}")
    print(f"project_root: {settings.project_root}")
    print(f"data_raw_dir: {settings.data_raw_dir}")
    print(f"data_processed_dir: {settings.data_processed_dir}")
    print(f"data_index_dir: {settings.data_index_dir}")
    print(
        "embedding_provider: "
        f"{embedding_provider.provider_name} ({embedding_provider.model_name})"
    )
    print(
        "generation_provider: "
        f"{generation_provider.provider_name} ({generation_provider.model_name})"
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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "handler"):
        return args.handler(args)

    print("book-research-agent scaffold is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Script to index CDD documentation into the vector store."""

import argparse
import sys
from pathlib import Path

from cdd_docs.config import get_settings
from cdd_docs.core.chunker import MarkdownChunker
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.vectorstore import VectorStore


def find_markdown_files(docs_path: Path) -> list[Path]:
    """Find all markdown files in the docs directory."""
    return list(docs_path.rglob("*.md"))


def main():
    """Main entry point for the indexing script."""
    parser = argparse.ArgumentParser(
        description="Index CDD documentation into the vector store"
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        help="Path to the CDD docs directory (overrides config)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the vector store before indexing",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print verbose output",
    )
    args = parser.parse_args()

    # Load settings
    settings = get_settings()
    docs_path = args.docs_path or settings.cdd_docs_path

    if not docs_path.exists():
        print(f"Error: Docs path does not exist: {docs_path}")
        sys.exit(1)

    print(f"Indexing documentation from: {docs_path}")
    print(f"Vector store path: {settings.vector_db_path}")
    print(f"Embedding model: {settings.embedding_model}")
    print()

    # Initialize components
    print("Loading embedding model...")
    embedder = Embedder(model_name=settings.embedding_model)
    print(f"  Model dimension: {embedder.dimension}")

    vector_store = VectorStore(
        persist_directory=settings.vector_db_path,
        collection_name=settings.collection_name,
    )

    if args.reset:
        print("Resetting vector store...")
        vector_store.reset()

    chunker = MarkdownChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # Find all markdown files
    md_files = find_markdown_files(docs_path)
    print(f"Found {len(md_files)} markdown files")
    print()

    # Process each file
    total_chunks = 0
    for file_path in md_files:
        relative_path = file_path.relative_to(docs_path)

        if args.verbose:
            print(f"Processing: {relative_path}")

        chunks = chunker.chunk_file(file_path, base_path=docs_path)

        if not chunks:
            if args.verbose:
                print(f"  No chunks generated (file too small)")
            continue

        # Embed all chunks
        texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(texts)

        # Add to vector store
        vector_store.add(
            ids=[chunk.id for chunk in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[chunk.metadata for chunk in chunks],
        )

        if args.verbose:
            print(f"  Added {len(chunks)} chunks")

        total_chunks += len(chunks)

    print()
    print(f"Indexing complete!")
    print(f"  Total files processed: {len(md_files)}")
    print(f"  Total chunks indexed: {total_chunks}")
    print(f"  Vector store count: {vector_store.count()}")


if __name__ == "__main__":
    main()

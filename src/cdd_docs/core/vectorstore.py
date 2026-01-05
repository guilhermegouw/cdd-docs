"""Vector store wrapper using ChromaDB."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings


class VectorStore:
    """Wrapper for ChromaDB vector database."""

    def __init__(
        self,
        persist_directory: Path | str,
        collection_name: str = "cdd_docs",
    ):
        """Initialize the vector store.

        Args:
            persist_directory: Directory to persist the database.
            collection_name: Name of the collection to use.
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self._collection = None

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to the collection.

        Args:
            ids: Unique identifiers for each document.
            documents: The document texts.
            embeddings: Pre-computed embeddings for each document.
            metadatas: Optional metadata for each document.
        """
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in ids],
        )

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents.

        Args:
            query_embedding: The query embedding vector.
            n_results: Number of results to return.
            where: Optional filter conditions.

        Returns:
            Dictionary containing ids, documents, metadatas, and distances.
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()

    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        self._collection = None

    def reset(self) -> None:
        """Reset the collection (delete and recreate)."""
        self.delete_collection()
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

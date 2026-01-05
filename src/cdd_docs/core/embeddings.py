"""Embedding model wrapper using sentence-transformers."""

from sentence_transformers import SentenceTransformer


class Embedder:
    """Wrapper for sentence-transformers embedding model."""

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """Initialize the embedder with the specified model.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Default is 'all-mpnet-base-v2' which provides good
                       quality embeddings for semantic search.
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def embed(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a batch.

        Args:
            texts: List of texts to embed.

        Returns:
            A list of embedding vectors.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self.model.get_sentence_embedding_dimension()

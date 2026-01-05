"""RAG pipeline for document Q&A."""

from dataclasses import dataclass

import anthropic
import httpx

from cdd_docs.config import Settings
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.vectorstore import VectorStore


@dataclass
class Source:
    """A source document used to answer a question."""

    file_path: str
    section: str
    text: str
    score: float


@dataclass
class Answer:
    """An answer from the RAG pipeline."""

    text: str
    sources: list[Source]


SYSTEM_PROMPT = """You are a documentation assistant for CDD (Context-Driven Development),
an AI-powered coding assistant CLI.

Your role is to answer questions about CDD's architecture, features, and usage based on
the provided documentation context.

Guidelines:
- Answer based ONLY on the provided context
- If the context doesn't contain enough information, say so clearly
- Reference specific files or sections when relevant
- Be concise but thorough
- Use code examples from the docs when helpful

If you cannot answer the question from the provided context, respond with:
"I couldn't find information about that in the documentation. You might want to check
[suggest where to look or ask to rephrase]."
"""


class RAGPipeline:
    """RAG pipeline combining retrieval and generation."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        settings: Settings,
    ):
        """Initialize the RAG pipeline.

        Args:
            embedder: The embedding model.
            vector_store: The vector database.
            settings: Application settings.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.settings = settings

        # Create Anthropic client with custom base URL for compatible providers
        self.client = anthropic.Anthropic(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(settings.llm_timeout, connect=10.0),
        )

    def search(self, query: str, top_k: int | None = None) -> list[Source]:
        """Search for relevant documents.

        Args:
            query: The search query.
            top_k: Number of results to return (defaults to settings.top_k).

        Returns:
            List of Source objects.
        """
        top_k = top_k or self.settings.top_k

        # Embed the query
        query_embedding = self.embedder.embed(query)

        # Search the vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k,
        )

        # Convert to Source objects
        sources = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            sources.append(
                Source(
                    file_path=meta.get("file_path", "unknown"),
                    section=meta.get("section", "unknown"),
                    text=doc,
                    score=1 - dist,  # Convert distance to similarity score
                )
            )

        return sources

    def ask(self, question: str, top_k: int | None = None) -> Answer:
        """Ask a question and get an answer with sources.

        Args:
            question: The question to answer.
            top_k: Number of source documents to retrieve.

        Returns:
            An Answer object with the response and sources.
        """
        # Retrieve relevant documents
        sources = self.search(question, top_k)

        if not sources:
            return Answer(
                text="I couldn't find any relevant documentation to answer your question.",
                sources=[],
            )

        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[Source {i}: {source.file_path} - {source.section}]\n{source.text}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Generate answer using Claude
        message = self.client.messages.create(
            model=self.settings.llm_model,
            max_tokens=self.settings.llm_max_tokens,
            temperature=self.settings.llm_temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\n---\n\nQuestion: {question}",
                }
            ],
        )

        # Extract text from all text blocks (skip thinking blocks, etc.)
        answer_parts = []
        for block in message.content:
            if hasattr(block, "text"):
                answer_parts.append(block.text)
        answer_text = "\n".join(answer_parts)

        return Answer(text=answer_text, sources=sources)

    async def ask_stream(self, question: str, top_k: int | None = None):
        """Ask a question and stream the answer.

        Args:
            question: The question to answer.
            top_k: Number of source documents to retrieve.

        Yields:
            Tuples of (chunk_type, content) where chunk_type is 'sources' or 'text'.
        """
        # Retrieve relevant documents
        sources = self.search(question, top_k)

        # Yield sources first
        yield ("sources", sources)

        if not sources:
            yield ("text", "I couldn't find any relevant documentation to answer your question.")
            return

        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[Source {i}: {source.file_path} - {source.section}]\n{source.text}"
            )
        context = "\n\n---\n\n".join(context_parts)

        # Stream answer using Claude
        with self.client.messages.stream(
            model=self.settings.llm_model,
            max_tokens=self.settings.llm_max_tokens,
            temperature=self.settings.llm_temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\n---\n\nQuestion: {question}",
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                yield ("text", text)

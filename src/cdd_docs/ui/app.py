"""Chainlit app for CDD Docs Agent."""

import chainlit as cl

from cdd_docs.config import get_settings
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.rag import RAGPipeline
from cdd_docs.core.vectorstore import VectorStore

# Global instances (initialized on startup)
rag_pipeline: RAGPipeline | None = None


@cl.on_chat_start
async def on_chat_start():
    """Initialize the RAG pipeline when a chat session starts."""
    global rag_pipeline

    if rag_pipeline is None:
        settings = get_settings()

        # Check if vector store has data
        vector_store = VectorStore(
            persist_directory=settings.vector_db_path,
            collection_name=settings.collection_name,
        )

        if vector_store.count() == 0:
            await cl.Message(
                content=(
                    "**Warning:** The vector store is empty. "
                    "Please run the indexing script first:\n\n"
                    "```bash\n"
                    "python -m cdd_docs.scripts.index\n"
                    "```"
                )
            ).send()
            return

        # Initialize components
        embedder = Embedder(model_name=settings.embedding_model)

        rag_pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            settings=settings,
        )

    await cl.Message(
        content=(
            "Welcome to the **CDD Docs Agent**!\n\n"
            "I can answer questions about CDD's architecture, features, and usage. "
            "Try asking things like:\n\n"
            "- How does the pub/sub system work?\n"
            "- What tools does the executor phase have access to?\n"
            "- How do I add a new slash command?\n"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages."""
    global rag_pipeline

    if rag_pipeline is None:
        await cl.Message(
            content="The RAG pipeline is not initialized. Please restart the app."
        ).send()
        return

    question = message.content

    # Create a message for streaming
    msg = cl.Message(content="")
    await msg.send()

    # Stream the response
    full_text = ""
    sources = []

    async for chunk_type, content in rag_pipeline.ask_stream(question):
        if chunk_type == "sources":
            sources = content
        elif chunk_type == "text":
            full_text += content
            await msg.stream_token(content)

    # Add sources as elements
    if sources:
        source_text = "\n\n---\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            source_text += f"\n{i}. `{source.file_path}` - {source.section} (score: {source.score:.2f})"

        await msg.stream_token(source_text)

    await msg.update()


@cl.on_stop
async def on_stop():
    """Handle stop signal."""
    pass

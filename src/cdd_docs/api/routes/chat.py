"""Chat API routes with SSE streaming."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from cdd_docs.api.models import ChatRequest, ChatResponse, Source
from cdd_docs.api.session import session_manager
from cdd_docs.config import get_settings
from cdd_docs.core.embeddings import Embedder
from cdd_docs.core.rag import RAGPipeline
from cdd_docs.core.vectorstore import VectorStore

router = APIRouter(prefix="/chat", tags=["chat"])

# Global RAG pipeline (initialized on first request)
_rag_pipeline: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or initialize the RAG pipeline."""
    global _rag_pipeline

    if _rag_pipeline is None:
        settings = get_settings()

        vector_store = VectorStore(
            persist_directory=settings.vector_db_path,
            collection_name=settings.collection_name,
        )

        if vector_store.count() == 0:
            raise HTTPException(
                status_code=503,
                detail="Vector store is empty. Please run the indexing script first.",
            )

        embedder = Embedder(model_name=settings.embedding_model)

        _rag_pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            settings=settings,
        )

    return _rag_pipeline


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Non-streaming chat endpoint for testing."""
    pipeline = get_rag_pipeline()

    # Get or create session
    session = session_manager.get_or_create(request.session_id)
    history = session_manager.get_history(session.id, pipeline.settings.max_history_turns)

    # Get answer
    answer = pipeline.ask(request.question, history=history)

    # Update session history
    session_manager.add_message(session.id, "user", request.question)
    session_manager.add_message(session.id, "assistant", answer.text)

    return ChatResponse(
        answer=answer.text,
        sources=[
            Source(file_path=s.file_path, section=s.section, score=s.score)
            for s in answer.sources
        ],
        session_id=session.id,
    )


async def generate_sse_stream(
    question: str,
    session_id: str | None,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for streaming chat response."""
    pipeline = get_rag_pipeline()

    # Get or create session
    session = session_manager.get_or_create(session_id)
    history = session_manager.get_history(session.id, pipeline.settings.max_history_turns)

    # Stream the response
    full_text = ""
    async for chunk_type, content in pipeline.ask_stream(question, history=history):
        if chunk_type == "sources":
            sources_data = [
                {"file_path": s.file_path, "section": s.section, "score": s.score}
                for s in content
            ]
            yield f"event: sources\ndata: {json.dumps(sources_data)}\n\n"
        elif chunk_type == "text":
            full_text += content
            yield f"event: text\ndata: {json.dumps(content)}\n\n"

    # Update session history
    session_manager.add_message(session.id, "user", question)
    session_manager.add_message(session.id, "assistant", full_text)

    # Send done event with session_id
    yield f"event: done\ndata: {json.dumps({'session_id': session.id})}\n\n"


@router.get("/stream")
async def chat_stream(
    question: str = Query(..., min_length=1, description="The question to ask"),
    session_id: str | None = Query(None, description="Optional session ID"),
) -> StreamingResponse:
    """Streaming chat endpoint using Server-Sent Events."""
    # Validate RAG pipeline is available
    get_rag_pipeline()

    return StreamingResponse(
        generate_sse_stream(question, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.delete("/{session_id}")
async def clear_session(session_id: str) -> dict:
    """Clear a chat session's history."""
    if session_manager.clear(session_id):
        return {"message": "Session cleared", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

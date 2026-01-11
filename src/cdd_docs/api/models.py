"""API request/response models."""

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A source document used to answer a question."""

    file_path: str
    section: str
    score: float


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    question: str = Field(..., min_length=1, description="The question to ask")
    session_id: str | None = Field(None, description="Optional session ID for conversation history")


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    answer: str
    sources: list[Source]
    session_id: str

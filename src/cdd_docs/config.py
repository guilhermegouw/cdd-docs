"""Configuration management for CDD Docs Agent."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    # Default to local docs folder in this repo
    # __file__ = src/cdd_docs/config.py -> .parent.parent.parent = cdd-docs/
    cdd_docs_path: Path = Path(__file__).parent.parent.parent / "docs"
    vector_db_path: Path = Path("./data/vectordb")

    # Embeddings
    embedding_model: str = "all-mpnet-base-v2"

    # LLM Provider (Anthropic-compatible)
    llm_api_key: str = ""  # API key or auth token
    llm_base_url: str = "https://api.minimax.io/anthropic"  # Anthropic-compatible endpoint
    llm_model: str = "MiniMax-M2"
    llm_max_tokens: int = 1024
    llm_timeout: float = 300.0  # seconds
    llm_temperature: float = 0.1  # Low temperature for factual, grounded responses

    # RAG (header-based chunking)
    min_chunk_size: int = 100  # words - sections smaller than this are skipped
    max_section_size: int = 1000  # words - warn if section exceeds this
    top_k: int = 7  # number of chunks to retrieve

    # Conversation History & Query Rewriting
    max_history_turns: int = 10  # number of conversation turns to keep
    enable_query_rewriting: bool = True  # rewrite queries using conversation context
    rewriter_max_tokens: int = 150  # max tokens for query rewriting
    rewriter_temperature: float = 0.3  # temperature for query rewriting

    # Collection
    collection_name: str = "cdd_docs"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

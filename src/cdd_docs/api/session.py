"""In-memory session manager for conversation history."""

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """A message in the conversation history."""

    role: Literal["user", "assistant"]
    content: str


@dataclass
class Session:
    """A chat session with conversation history."""

    id: str
    history: list[ChatMessage] = field(default_factory=list)
    last_accessed: float = field(default_factory=time.time)


class SessionManager:
    """Manages chat sessions with TTL cleanup."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize the session manager.

        Args:
            ttl_seconds: Time-to-live for sessions in seconds (default: 1 hour).
        """
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def get_or_create(self, session_id: str | None = None) -> Session:
        """Get an existing session or create a new one.

        Args:
            session_id: Optional session ID. If None, creates a new session.

        Returns:
            The session object.
        """
        with self._lock:
            self._cleanup_stale()

            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_accessed = time.time()
                return session

            # Create new session
            new_id = session_id or str(uuid.uuid4())
            session = Session(id=new_id)
            self._sessions[new_id] = session
            return session

    def add_message(self, session_id: str, role: Literal["user", "assistant"], content: str):
        """Add a message to a session's history.

        Args:
            session_id: The session ID.
            role: The message role.
            content: The message content.
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.history.append({"role": role, "content": content})
                session.last_accessed = time.time()

    def get_history(self, session_id: str, max_turns: int = 10) -> list[ChatMessage]:
        """Get conversation history for a session.

        Args:
            session_id: The session ID.
            max_turns: Maximum number of conversation turns to return.

        Returns:
            List of chat messages (limited to max_turns * 2 messages).
        """
        with self._lock:
            if session_id not in self._sessions:
                return []
            max_messages = max_turns * 2
            return self._sessions[session_id].history[-max_messages:]

    def clear(self, session_id: str) -> bool:
        """Clear a session's history.

        Args:
            session_id: The session ID.

        Returns:
            True if session existed and was cleared.
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def _cleanup_stale(self):
        """Remove sessions that haven't been accessed within TTL."""
        now = time.time()
        stale = [
            sid for sid, session in self._sessions.items()
            if now - session.last_accessed > self._ttl
        ]
        for sid in stale:
            del self._sessions[sid]


# Global session manager instance
session_manager = SessionManager()

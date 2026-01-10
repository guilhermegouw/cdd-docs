"""Markdown document chunker for RAG indexing."""

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text from a markdown document."""

    id: str
    text: str
    metadata: dict

    @property
    def file_path(self) -> str:
        return self.metadata.get("file_path", "")

    @property
    def section(self) -> str:
        return self.metadata.get("section", "")


class MarkdownChunker:
    """Chunker that splits markdown documents by headers.

    Uses pure header-based chunking to keep semantic sections intact,
    preserving diagrams and explanatory text together.
    """

    def __init__(
        self,
        min_chunk_size: int = 100,
        max_section_size: int = 1000,
    ):
        """Initialize the chunker.

        Args:
            min_chunk_size: Minimum size of a chunk in words. Sections smaller
                than this will be skipped.
            max_section_size: Warn if a section exceeds this many words.
                Consider breaking large sections into subsections.
        """
        self.min_chunk_size = min_chunk_size
        self.max_section_size = max_section_size

    def chunk_file(self, file_path: Path, base_path: Path | None = None) -> list[Chunk]:
        """Chunk a markdown file into pieces.

        Args:
            file_path: Path to the markdown file.
            base_path: Base path for computing relative paths in metadata.

        Returns:
            List of Chunk objects.
        """
        content = file_path.read_text(encoding="utf-8")
        relative_path = (
            str(file_path.relative_to(base_path)) if base_path else str(file_path)
        )

        return self.chunk_text(content, relative_path)

    def chunk_text(self, text: str, source_path: str = "") -> list[Chunk]:
        """Chunk markdown text into pieces.

        Args:
            text: The markdown text to chunk.
            source_path: Source file path for metadata.

        Returns:
            List of Chunk objects.
        """
        # Split by headers
        sections = self._split_by_headers(text)
        chunks = []

        for section_title, section_content in sections:
            section_chunks = self._chunk_section(
                section_content,
                source_path,
                section_title,
            )
            chunks.extend(section_chunks)

        return chunks

    def _split_by_headers(self, text: str) -> list[tuple[str, str]]:
        """Split text by markdown headers.

        Returns list of (header_title, content) tuples.
        """
        # Pattern to match headers (# Header, ## Header, etc.)
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        sections = []
        last_end = 0
        current_header = "Introduction"

        for match in header_pattern.finditer(text):
            # Get content before this header
            content = text[last_end : match.start()].strip()
            if content:
                sections.append((current_header, content))

            # Update for next section
            current_header = match.group(2).strip()
            last_end = match.end()

        # Don't forget the last section
        remaining = text[last_end:].strip()
        if remaining:
            sections.append((current_header, remaining))

        return sections

    def _chunk_section(
        self,
        content: str,
        source_path: str,
        section_title: str,
    ) -> list[Chunk]:
        """Create a single chunk for the entire section.

        Uses pure header-based chunking - each section becomes one chunk
        to keep diagrams and explanatory text together.
        """
        words = content.split()
        word_count = len(words)

        # Skip sections that are too small
        if word_count < self.min_chunk_size:
            return []

        # Warn if section is unusually large
        if word_count > self.max_section_size:
            logger.warning(
                "Large section detected: '%s' in %s has %d words (max recommended: %d). "
                "Consider breaking into subsections.",
                section_title,
                source_path,
                word_count,
                self.max_section_size,
            )

        return [self._create_chunk(content, source_path, section_title, 0)]

    def _create_chunk(
        self,
        text: str,
        source_path: str,
        section: str,
        index: int,
    ) -> Chunk:
        """Create a Chunk object with computed ID and metadata."""
        # Create a unique ID based on content and location
        id_source = f"{source_path}:{section}:{index}:{text[:100]}"
        chunk_id = hashlib.sha256(id_source.encode()).hexdigest()[:16]

        return Chunk(
            id=chunk_id,
            text=text,
            metadata={
                "file_path": source_path,
                "section": section,
                "chunk_index": index,
            },
        )

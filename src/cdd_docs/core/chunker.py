"""Markdown document chunker for RAG indexing."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


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
    """Chunker that splits markdown documents by headers and size."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """Initialize the chunker.

        Args:
            chunk_size: Target size of each chunk in words.
            chunk_overlap: Number of words to overlap between chunks.
            min_chunk_size: Minimum size of a chunk in words.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

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
        """Chunk a single section into appropriately sized pieces."""
        words = content.split()

        if len(words) <= self.chunk_size:
            # Small enough to be a single chunk
            if len(words) >= self.min_chunk_size:
                return [
                    self._create_chunk(content, source_path, section_title, 0)
                ]
            return []

        # Split into overlapping chunks
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            if len(chunk_words) >= self.min_chunk_size:
                chunks.append(
                    self._create_chunk(chunk_text, source_path, section_title, chunk_index)
                )
                chunk_index += 1

            start = end - self.chunk_overlap
            if start >= len(words) - self.min_chunk_size:
                break

        return chunks

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

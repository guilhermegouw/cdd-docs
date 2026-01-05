"""Tests for the markdown chunker."""

import pytest

from cdd_docs.core.chunker import MarkdownChunker


class TestMarkdownChunker:
    """Tests for MarkdownChunker."""

    def test_chunk_simple_text(self):
        """Test chunking simple text without headers."""
        chunker = MarkdownChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=10)
        text = " ".join(["word"] * 100)  # 100 words

        chunks = chunker.chunk_text(text, "test.md")

        assert len(chunks) > 1
        assert all(chunk.metadata["file_path"] == "test.md" for chunk in chunks)

    def test_chunk_with_headers(self):
        """Test chunking text with markdown headers."""
        chunker = MarkdownChunker(chunk_size=100, chunk_overlap=10, min_chunk_size=10)
        text = """# Main Title

This is the introduction section with some content.

## First Section

This is the first section with more detailed content about the topic.

## Second Section

This is the second section with different content.

### Subsection

This is a subsection with additional details.
"""
        chunks = chunker.chunk_text(text, "test.md")

        # Should have multiple chunks with different sections
        sections = {chunk.section for chunk in chunks}
        assert "Main Title" in sections or "First Section" in sections

    def test_chunk_preserves_metadata(self):
        """Test that chunks have correct metadata."""
        chunker = MarkdownChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=10)
        text = """# Test Header

This is some content under the test header with enough words to create a chunk.
"""
        chunks = chunker.chunk_text(text, "path/to/file.md")

        assert len(chunks) >= 1
        chunk = chunks[0]
        assert chunk.metadata["file_path"] == "path/to/file.md"
        assert "section" in chunk.metadata
        assert "chunk_index" in chunk.metadata

    def test_small_file_not_chunked(self):
        """Test that very small content is not chunked."""
        chunker = MarkdownChunker(chunk_size=100, chunk_overlap=10, min_chunk_size=50)
        text = "Just a few words."  # Less than min_chunk_size

        chunks = chunker.chunk_text(text, "test.md")

        assert len(chunks) == 0

    def test_unique_chunk_ids(self):
        """Test that chunk IDs are unique."""
        chunker = MarkdownChunker(chunk_size=30, chunk_overlap=5, min_chunk_size=10)
        text = " ".join(["word"] * 200)

        chunks = chunker.chunk_text(text, "test.md")

        ids = [chunk.id for chunk in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs should be unique"

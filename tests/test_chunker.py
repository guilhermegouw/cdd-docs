"""Tests for the markdown chunker."""

import logging

import pytest

from cdd_docs.core.chunker import MarkdownChunker


class TestMarkdownChunker:
    """Tests for MarkdownChunker."""

    def test_chunk_simple_text(self):
        """Test chunking simple text without headers produces single chunk."""
        chunker = MarkdownChunker(min_chunk_size=10)
        text = " ".join(["word"] * 100)  # 100 words

        chunks = chunker.chunk_text(text, "test.md")

        # Header-based chunking: text without headers becomes one "Introduction" chunk
        assert len(chunks) == 1
        assert chunks[0].metadata["file_path"] == "test.md"
        assert chunks[0].section == "Introduction"

    def test_chunk_with_headers(self):
        """Test chunking text with markdown headers creates one chunk per section."""
        chunker = MarkdownChunker(min_chunk_size=5)
        text = """# Main Title

This is the introduction section with some content here.

## First Section

This is the first section with more detailed content about the topic at hand.

## Second Section

This is the second section with different content for testing purposes.

### Subsection

This is a subsection with additional details and more words to meet minimum.
"""
        chunks = chunker.chunk_text(text, "test.md")

        # Header-based chunking: one chunk per section (that meets min size)
        sections = {chunk.section for chunk in chunks}
        assert "Main Title" in sections
        assert "First Section" in sections
        assert "Second Section" in sections
        assert "Subsection" in sections

    def test_chunk_preserves_metadata(self):
        """Test that chunks have correct metadata."""
        chunker = MarkdownChunker(min_chunk_size=5)
        text = """# Test Header

This is some content under the test header with enough words to create a chunk.
"""
        chunks = chunker.chunk_text(text, "path/to/file.md")

        assert len(chunks) == 1
        chunk = chunks[0]
        assert chunk.metadata["file_path"] == "path/to/file.md"
        assert chunk.metadata["section"] == "Test Header"
        assert chunk.metadata["chunk_index"] == 0

    def test_small_section_skipped(self):
        """Test that sections smaller than min_chunk_size are skipped."""
        chunker = MarkdownChunker(min_chunk_size=50)
        text = "Just a few words."  # Less than min_chunk_size

        chunks = chunker.chunk_text(text, "test.md")

        assert len(chunks) == 0

    def test_unique_chunk_ids_across_sections(self):
        """Test that chunk IDs are unique across different sections."""
        chunker = MarkdownChunker(min_chunk_size=5)
        text = """# Section One

Content for section one with enough words.

## Section Two

Content for section two with enough words.

## Section Three

Content for section three with enough words.
"""
        chunks = chunker.chunk_text(text, "test.md")

        ids = [chunk.id for chunk in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs should be unique"
        assert len(chunks) == 3

    def test_large_section_warning(self, caplog):
        """Test that large sections trigger a warning."""
        chunker = MarkdownChunker(min_chunk_size=5, max_section_size=50)
        text = "# Big Section\n\n" + " ".join(["word"] * 100)  # 100 words, exceeds max

        with caplog.at_level(logging.WARNING):
            chunks = chunker.chunk_text(text, "test.md")

        assert len(chunks) == 1  # Still creates the chunk
        assert "Large section detected" in caplog.text
        assert "Big Section" in caplog.text

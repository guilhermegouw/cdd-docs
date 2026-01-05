# CDD Docs Agent

A RAG-powered documentation assistant for the [CDD (Context-Driven Development)](https://github.com/guilhermegouw/cdd) project.

## Overview

This agent indexes CDD's markdown documentation and provides a chat interface to query it using natural language. It uses:

- **Embeddings**: sentence-transformers (local, free)
- **Vector Store**: ChromaDB (local, persistent)
- **LLM**: Any Anthropic-compatible API (Minimax M2, GLM, Claude, etc.)
- **UI**: Chainlit (web-based chat)

## Quick Start

### 1. Install dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e ".[dev]"
```

### 2. Configure

```bash
# Copy the example config
cp .env.example .env

# Edit .env and add your Anthropic API key
```

### 3. Index the documentation

```bash
# Index CDD docs (uses default path ~/code/cdd/docs)
python -m cdd_docs.scripts.index

# Or specify a custom path
python -m cdd_docs.scripts.index --docs-path /path/to/cdd/docs

# Use --verbose to see what's being indexed
python -m cdd_docs.scripts.index --verbose

# Use --reset to clear and rebuild the index
python -m cdd_docs.scripts.index --reset
```

### 4. Start the chat UI

```bash
# Run the Chainlit app
chainlit run src/cdd_docs/ui/app.py --port 8000

# Or use the convenience script
python -m cdd_docs.scripts.serve
```

Open http://localhost:8000 in your browser.

## Project Structure

```
cdd-docs/
├── src/cdd_docs/
│   ├── config.py           # Configuration management
│   ├── core/
│   │   ├── embeddings.py   # Embedding model wrapper
│   │   ├── vectorstore.py  # ChromaDB wrapper
│   │   ├── chunker.py      # Markdown chunking
│   │   └── rag.py          # RAG pipeline
│   ├── scripts/
│   │   ├── index.py        # Indexing script
│   │   └── serve.py        # Serve script
│   └── ui/
│       └── app.py          # Chainlit app
├── data/
│   └── vectordb/           # Persistent vector store (created on indexing)
├── tests/
├── pyproject.toml
└── README.md
```

## Configuration

All settings can be configured via environment variables or `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` | API key or auth token (required) | - |
| `LLM_BASE_URL` | Anthropic-compatible API endpoint | `https://api.minimax.io/anthropic` |
| `LLM_MODEL` | Model name to use | `MiniMax-M2` |
| `LLM_TIMEOUT` | Request timeout in seconds | `300.0` |
| `CDD_DOCS_PATH` | Path to CDD docs directory | `~/code/cdd/docs` |
| `VECTOR_DB_PATH` | Path to vector database | `./data/vectordb` |
| `EMBEDDING_MODEL` | sentence-transformers model | `all-mpnet-base-v2` |
| `CHUNK_SIZE` | Target chunk size in words | `500` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `TOP_K` | Number of chunks to retrieve | `5` |

### Supported Providers

Any Anthropic-compatible API works. Examples:

```bash
# Minimax M2 (default)
LLM_BASE_URL=https://api.minimax.io/anthropic
LLM_MODEL=MiniMax-M2

# GLM
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4

# Anthropic Claude (direct)
LLM_BASE_URL=https://api.anthropic.com
LLM_MODEL=claude-sonnet-4-20250514
```

## Example Queries

Once running, try asking:

- "How does the pub/sub system work?"
- "What tools does the executor phase have access to?"
- "How do I add a new slash command?"
- "What's the difference between PhaseAgent and AgentInstance?"
- "Explain the layered architecture"
- "What are the CDD workflow phases?"

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Format code
ruff format src/
```

## How It Works

1. **Indexing**: The indexer reads all `.md` files from the CDD docs directory, splits them into chunks by headers and size, generates embeddings using sentence-transformers, and stores them in ChromaDB.

2. **Querying**: When you ask a question, the system:
   - Embeds your question using the same model
   - Searches for the most similar chunks in the vector store
   - Sends the relevant chunks as context to Claude
   - Streams the answer back to you

3. **Sources**: Each answer includes the source files and sections used, with relevance scores.

## Future Improvements

- [ ] Add MCP server for Claude Code integration
- [ ] Support multiple branches (main vs feature branches)
- [ ] Add evaluation metrics for retrieval quality
- [ ] Experiment with different chunking strategies
- [ ] Add hybrid search (keyword + semantic)

## License

MIT

# CDD Docs Agent

A RAG-powered documentation assistant for the [CDD (Context-Driven Development)](https://github.com/guilhermegouw/cdd) project.

## Overview

This agent indexes CDD's markdown documentation and provides a chat interface to query it using natural language. It uses:

- **Embeddings**: sentence-transformers (local, free)
- **Vector Store**: ChromaDB (local, persistent)
- **LLM**: Any Anthropic-compatible API (Minimax M2, GLM, Claude, etc.)
- **Backend**: FastAPI with SSE streaming
- **Frontend**: React with Mermaid diagram support

## Features

- Natural language Q&A over documentation
- Conversation history with query rewriting
- Mermaid diagram rendering with automatic syntax validation and fixing
- Real-time streaming responses
- Source attribution with relevance scores

## Quick Start

### 1. Install Python dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e ".[dev]"
```

### 2. Install Node.js dependencies

```bash
# Install frontend dependencies
cd frontend
npm install
cd ..

# Install mermaid CLI globally (for diagram validation)
npm install -g @mermaid-js/mermaid-cli@10.9.1
```

### 3. Configure

```bash
# Copy the example config
cp .env.example .env

# Edit .env and add your API key
```

### 4. Index the documentation

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

### 5. Start the application

You need to run both the backend and frontend:

**Terminal 1 - Backend (FastAPI):**
```bash
source .venv/bin/activate
python -m cdd_docs.scripts.serve
```

**Terminal 2 - Frontend (React):**
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Project Structure

```
cdd-docs/
├── src/cdd_docs/
│   ├── config.py           # Configuration management
│   ├── core/
│   │   ├── embeddings.py   # Embedding model wrapper
│   │   ├── vectorstore.py  # ChromaDB wrapper
│   │   ├── chunker.py      # Markdown chunking
│   │   ├── rag.py          # RAG pipeline with mermaid validation
│   │   └── mermaid.py      # Mermaid diagram validation
│   ├── api/
│   │   ├── main.py         # FastAPI application
│   │   ├── routes/
│   │   │   └── chat.py     # Chat endpoints (REST + SSE)
│   │   ├── models.py       # Pydantic models
│   │   └── session.py      # Session management
│   └── scripts/
│       ├── index.py        # Indexing script
│       └── serve.py        # Backend server script
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── MarkdownRenderer.tsx  # Mermaid support
│   │   └── hooks/
│   │       └── useChat.ts  # Chat state management
│   └── package.json
├── docs/                   # C4 architecture documentation
├── data/
│   └── vectordb/           # Persistent vector store
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
| `TOP_K` | Number of chunks to retrieve | `5` |
| `ENABLE_QUERY_REWRITING` | Enable conversation-aware queries | `true` |
| `MAX_HISTORY_TURNS` | Conversation turns to keep | `5` |

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

## Mermaid Diagram Support

The agent can include and adapt Mermaid diagrams from the documentation:

- Diagrams are rendered in real-time in the chat UI
- Syntax validation using the official `mmdc` CLI
- Automatic fix loop: if a diagram has syntax errors, the agent is asked to fix them (up to 2 retries)
- Falls back to showing raw code if rendering fails

**Requirements:**
- `@mermaid-js/mermaid-cli@10.9.1` installed globally (for validation)
- Frontend uses `mermaid@10.9.5` (versions are aligned)

## Example Queries

Once running, try asking:

- "How does the pub/sub system work?"
- "What tools does the executor phase have access to?"
- "How do I add a new slash command?"
- "What's the difference between PhaseAgent and AgentInstance?"
- "Explain the layered architecture"
- "Show me the data flow diagram"

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Non-streaming chat (for testing) |
| `/chat/stream` | GET | SSE streaming chat |
| `/chat/{session_id}` | DELETE | Clear session history |

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

# Frontend dev server with hot reload
cd frontend && npm run dev
```

## How It Works

1. **Indexing**: The indexer reads all `.md` files from the CDD docs directory, splits them into chunks by headers, generates embeddings using sentence-transformers, and stores them in ChromaDB.

2. **Querying**: When you ask a question, the system:
   - Rewrites your query using conversation history for context
   - Embeds your question using the same model
   - Searches for the most similar chunks in the vector store
   - Sends the relevant chunks as context to the LLM
   - Validates any Mermaid diagrams in the response
   - Streams the answer back to you

3. **Sources**: Each answer includes the source files and sections used, with relevance scores.

## License

MIT

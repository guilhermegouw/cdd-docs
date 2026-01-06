# Lessons Learned

This file captures learnings from building and improving the CDD documentation agent. Reference this in future sessions to avoid repeating mistakes.

## RAG Documentation Best Practices

### Document Structure

| Do | Don't |
|----|-------|
| Use 100+ words per section | Create many tiny sections (<100 words) |
| Consolidate related content under one header | Split content across many `###` sub-headers |
| Use **bold text** for sub-topics within a section | Use headers for every small piece of content |
| Keep diagrams with their explanatory text | Isolate diagrams in their own sections |

### Section Titles and Opening Sentences

**Section titles should match how users ask questions:**
- Bad: "Configuration Examples"
- Good: "Configuration File Format and Examples"

**Opening sentences should contain key phrases users would search for:**
```markdown
## Configuration File Format and Examples

This section shows what the CDD configuration JSON file looks like in practice...
```

### Code Blocks

**Avoid bash comments that look like markdown headers:**
```bash
# This looks like a header to the chunker!
cdd providers list
```

Instead, use inline comments or descriptive prose:
```markdown
Use `cdd providers list` to see all available providers.
```

### Chunking Configuration

| Parameter | Our Setting | Notes |
|-----------|-------------|-------|
| `chunk_size` | 200 words | Smaller = better precision per chunk |
| `chunk_overlap` | 30 words | Helps with context continuity |
| `min_chunk_size` | 100 words | Sections below this are DROPPED |
| `top_k` | 7 | Retrieves 7 most relevant chunks |

**Key insight:** Document structure matters MORE than chunking parameters. Restructuring the doc improved scores more than tuning chunk_size or top_k.

## Evaluation Process

1. Create eval cases with expected keywords and sources
2. Run evaluation: `python -m cdd_docs.scripts.evaluate eval_cases/<file>.json`
3. Check which questions fail
4. Debug retrieval to see which chunks are being returned
5. Fix documentation structure, not just RAG parameters

### Debugging Retrieval

```python
# Check what chunks exist
python3 << 'EOF'
from cdd_docs.config import get_settings
from cdd_docs.core.vectorstore import VectorStore
from cdd_docs.core.embeddings import Embedder

settings = get_settings()
vs = VectorStore(persist_directory=settings.vector_db_path, collection_name=settings.collection_name)
embedder = Embedder(model_name=settings.embedding_model)

query = "Your question here"
query_embedding = embedder.embed(query)
results = vs.search(query_embedding, n_results=10)

for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
    print(f"{i+1}. {meta.get('section')} - score={1-dist:.2f}")
EOF
```

## Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Section too small | Content not in chunks | Expand to 100+ words or merge with related section |
| Poor retrieval | Right doc, wrong chunk retrieved | Improve section title and opening sentence |
| Code comments parsed as headers | Chunks split unexpectedly | Use prose or inline comments instead of `# comment` |
| Question not matching content | Low similarity scores | Add natural language phrases users would search for |

## Session History

### 2026-01-06: Initial Config Module Documentation
- Created `docs/features/config-module.md` for configuration flow
- Discovered chunking issues (42 sections → only 4 chunks indexed)
- Restructured to 12 substantial sections
- Improved eval scores: 69.7% → 98.2%
- Fixed bash comment parsing issue
- Added semantic matching phrases to section titles

# Repository Agent Instructions

## Project
- Python 3.11+ agentic assistant: Gemini/Ollama Week 1 tools plus Week 2 document RAG.
- Week 2 uses Gemini embeddings, persistent local Chroma, SQLite user memory, citations, refusals, and conversation compaction.

## Setup
- Run uv sync --extra dev.
- Copy .env.example to .env and set LLM_API_KEY privately.
- Never commit .env, API keys, uploaded files, .data, vector indexes, or personal memory databases.

## Commands
- Terminal agent: uv run agentic-assistant
- Offline smoke demo: uv run agentic-assistant --demo
- Streamlit UI: uv run streamlit run app.py
- Index samples: uv run python scripts/ingest_samples.py
- Embed ten sentences: uv run python scripts/embed_ten_sentences.py
- Evaluate: uv run python scripts/run_rag_eval.py
- Compare chunk sizes: uv run python scripts/compare_chunk_sizes.py
- Tests: uv run pytest
- Lint: uv run ruff check .

## Architecture rules
- Keep extraction, chunking, embeddings, vector storage, memory, and orchestration separated.
- Validate all model-supplied tool arguments with Pydantic.
- Bind user_id in trusted application code; never let the model select another user's ID.
- Tool names/descriptions must be narrow, explicit, non-overlapping, and testable.
- Return compact tool output with limits and useful errors.
- Factual RAG answers require citations from retrieved sources; reject unknown citation IDs.
- Refuse when evidence is insufficient.
- Preserve filename, page, and chunk index in metadata.
- When compacting, preserve newest complete turns and summarize older conversation only.
- Use parameterized SQL, request timeouts, and bounded agent loops.
- Never log secrets or full private memory/document content.

## Quality gates
- Add deterministic tests for chunking, source metadata, per-user isolation, schema validation, citations, refusals, and compaction.
- Run pytest and ruff before release.
- Live embedding/generation results must be produced against the configured provider; never fabricate them.

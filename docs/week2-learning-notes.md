# Week 2 Learning Notes — Context, Memory and RAG

## Five rules for effective agent tools
1. Give each tool one narrow responsibility and avoid overlapping tools.
2. Use clear action/resource names and descriptions that state when to call the tool.
3. Validate unambiguous inputs with required fields and sensible length limits.
4. Return compact, filtered results; cap large outputs and use useful error messages.
5. Evaluate tool selection, arguments, output quality, and error recovery with repeatable cases.

These points follow Anthropic's guidance on tool choice, clear boundaries, meaningful outputs, token efficiency, and tool specifications.

## Embeddings and cosine similarity
An embedding maps text to a numeric vector. Cosine similarity measures the angle between two vectors: dot(A,B) / (norm(A) × norm(B)). A larger cosine similarity indicates greater directional similarity. Gemini gemini-embedding-001 supports SEMANTIC_SIMILARITY for pair comparison, RETRIEVAL_DOCUMENT for indexed passages, and RETRIEVAL_QUERY for incoming search queries.

Run uv run python scripts/embed_ten_sentences.py to embed ten sentences, compare all pairs, report the most similar pair, and store/query the vectors and metadata in Chroma.

## Context rot — three sentences
Context rot is a reduction in an LLM's ability to accurately retrieve information as the context becomes longer. Repeated tool output, irrelevant history, and duplicated information compete with the details needed for the current task. Context engineering keeps high-value information, retrieves only relevant documents, and summarizes older conversation while preserving recent turns.

## Chroma and the RAG pipeline
The ingestion path extracts documents, splits text into overlapping chunks, attaches filename/page metadata, embeds each chunk, and persists the vectors and text in Chroma. At question time, the query is embedded and the nearest chunks are retrieved; the model answers only from those passages. Each source ID maps to a filename, page, and chunk index so citations can be checked against the original document.

This project calls Chroma PersistentClient for local persistence and uses cosine distance for nearest-neighbour search. A lower distance corresponds to a closer vector.

## AGENTS.md and Agent Skills
AGENTS.md is a repository-level Markdown file for coding-agent instructions such as setup commands, tests, architecture, code style, and security limits. Agent Skills use a directory containing a required SKILL.md with YAML frontmatter fields name and description, followed by Markdown instructions; optional scripts, references, and assets directories support progressive disclosure.

## References
- Anthropic, Writing effective tools for agents: https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Google, Gemini embeddings: https://ai.google.dev/gemini-api/docs/embeddings
- Chroma, Getting started: https://docs.trychroma.com/
- AGENTS.md: https://agents.md/
- Agent Skills specification: https://agentskills.io/specification

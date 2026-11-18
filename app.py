"""Streamlit UI for the Week 2 document assistant."""
from __future__ import annotations
import os
import re
import uuid
from pathlib import Path
import streamlit as st
from agentic_assistant.agent import build_client
from agentic_assistant.context import estimate_tokens
from agentic_assistant.config import load_settings
from agentic_assistant.documents import load_and_chunk
from agentic_assistant.embeddings import GeminiEmbeddings
from agentic_assistant.memory import UserMemoryStore
from agentic_assistant.rag import DocumentAssistant
from agentic_assistant.vector_store import ChromaIndex

ROOT = Path(__file__).parent
DATA = ROOT / ".data"

@st.cache_resource
def backend():
    settings = load_settings()
    if settings.provider != "gemini":
        raise RuntimeError("Week 2 embeddings currently require the Gemini API key; Ollama can still be used for Week 1.")
    embedder = GeminiEmbeddings(settings.api_key, model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"))
    index = ChromaIndex(DATA / "chroma", embedder)
    memory = UserMemoryStore(DATA / "user-memory.db")
    assistant = DocumentAssistant(
        build_client(settings), settings.model, index, memory,
        provider=settings.provider, temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        max_history_tokens=int(os.getenv("MAX_HISTORY_TOKENS", "2200")),
        min_similarity=float(os.getenv("RAG_MIN_SIMILARITY", "0.35")),
    )
    return settings, index, memory, assistant

def save_upload(upload):
    folder = DATA / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(upload.name).name)
    path = folder / (uuid.uuid4().hex[:8] + "-" + safe)
    path.write_bytes(upload.getvalue())
    return path

def main():
    st.set_page_config(page_title="Document Assistant with Memory", page_icon="📚", layout="wide")
    st.title("Document Assistant with Memory")
    st.caption("Persistent RAG • source citations • user-scoped memory • context compaction")
    try:
        settings, index, memory, assistant = backend()
    except Exception as exc:
        st.error(f"Cannot start: {type(exc).__name__}: {exc}")
        st.info("Check .env and run uv sync --extra dev.")
        st.stop()

    st.session_state.setdefault("user_id", "local-user")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("last_compaction", None)

    with st.sidebar:
        st.header("Workspace")
        st.caption(f"Provider: {settings.provider} | Model: {settings.model}")
        st.warning("Local demo only: this editable ID is not authentication. A deployed multi-user app must bind an authenticated account ID on the server.")
        new_id = st.text_input("Pseudonymous local user ID", st.session_state.user_id).strip()
        if new_id and new_id != st.session_state.user_id:
            st.session_state.user_id = new_id
            st.session_state.messages = []
            st.rerun()

        st.metric("Indexed document chunks", index.count())
        files = st.file_uploader(
            "Upload PDF, DOCX, TXT, or MD", type=["pdf","docx","txt","md"],
            accept_multiple_files=True,
        )
        if st.button("Index uploaded documents", disabled=not files, use_container_width=True):
            try:
                with st.spinner("Extracting, chunking, embedding, and storing..."):
                    paths = [save_upload(item) for item in files or []]
                    chunks = load_and_chunk(paths)
                    count = index.upsert_chunks(chunks)
                st.success(f"Stored {count} chunks from {len(paths)} files.")
                st.rerun()
            except Exception as exc:
                st.error(f"Ingestion failed: {type(exc).__name__}: {exc}")

        if st.button("Index six sample documents", use_container_width=True):
            try:
                with st.spinner("Indexing sample knowledge base..."):
                    chunks = load_and_chunk([ROOT / "examples" / "docs"])
                    count = index.upsert_chunks(chunks)
                st.success(f"Stored {count} sample chunks.")
                st.rerun()
            except Exception as exc:
                st.error(f"Sample indexing failed: {type(exc).__name__}: {exc}")

        st.divider()
        st.subheader("Long-term memory")
        key = st.text_input("Memory key", placeholder="preferred_style")
        value = st.text_area("Memory value", placeholder="Prefers concise explanations.")
        if st.button("Save memory"):
            try:
                memory.save(st.session_state.user_id, key, value)
                st.success("Memory saved.")
            except ValueError as exc:
                st.error(str(exc))
        saved = memory.load_for_user(st.session_state.user_id)
        with st.expander(f"View saved memories ({len(saved)})"):
            for item in saved:
                st.markdown("**" + item["memory_key"] + "**")
                st.write(item["memory_value"])
                if st.button("Forget " + item["memory_key"], key="forget_" + item["memory_key"]):
                    memory.forget(st.session_state.user_id, item["memory_key"])
                    st.rerun()
        if st.button("Clear conversation"):
            st.session_state.messages = []
            st.session_state.last_compaction = None
            st.rerun()

        history_tokens = estimate_tokens(st.session_state.messages)
        st.caption(
            f"Conversation history: {history_tokens:,} estimated tokens / "
            f"{assistant.max_history_tokens:,} token threshold."
        )
        can_compact = (
            history_tokens > assistant.max_history_tokens
            and len(st.session_state.messages) > assistant.keep_recent_messages
        )
        if st.button(
            "Compact conversation history",
            disabled=not can_compact,
            use_container_width=True,
        ):
            try:
                metric = assistant.compact_conversation(st.session_state.messages)
                if metric["compacted"]:
                    st.session_state.messages = metric["messages"]
                    st.session_state.last_compaction = metric
                    st.rerun()
                st.info("Add more conversation history before compacting.")
            except Exception as exc:
                st.error(f"Compaction failed: {type(exc).__name__}: {exc}")

    if index.count() == 0:
        st.warning("Index the six sample documents or upload your own documents before asking document questions.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    metric = st.session_state.last_compaction
    if metric:
        st.caption(
            f"History tokens (estimated): {metric['before_tokens']} → {metric['after_tokens']} "
            f"({metric['reduction_percent']}% reduction; cl100k_base or fallback estimate)."
        )

    question = st.chat_input("Ask a question about the indexed documents...")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving sources and generating a grounded answer..."):
                try:
                    result = assistant.ask(
                        question, user_id=st.session_state.user_id,
                        history=st.session_state.messages,
                    )
                except Exception as exc:
                    st.error(f"Request failed: {type(exc).__name__}: {exc}")
                    st.stop()
            if result.answer.refused:
                st.warning(result.answer.answer)
            else:
                st.markdown(result.answer.answer)
            if result.sources:
                st.markdown("**Citations**")
                for source in result.sources:
                    st.caption(
                        f"[{source['id']}] {source['source']} · page {source['page']} "
                        f"· chunk {source['chunk_index']} · similarity {source['similarity']}"
                    )
            if result.tools_used:
                st.caption("Memory tools executed: " + ", ".join(result.tools_used))
        state = list(result.history)
        if state:
            assistant_text = state[-1]["content"]
            if result.answer.citations:
                assistant_text += "\n\nSources: " + ", ".join(result.answer.citations)
            state[-1] = {"role":"assistant","content":assistant_text}
        st.session_state.messages = state
        st.session_state.last_compaction = result.compaction
        st.rerun()

if __name__ == "__main__":
    main()

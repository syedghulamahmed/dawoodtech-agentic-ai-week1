"""Ingest the six sample documents into persistent Chroma."""
from pathlib import Path
from agentic_assistant.config import load_settings
from agentic_assistant.documents import load_and_chunk
from agentic_assistant.embeddings import GeminiEmbeddings
from agentic_assistant.vector_store import ChromaIndex

def main():
    settings = load_settings()
    chunks = load_and_chunk([Path("examples/docs")], chunk_size=900, overlap=120)
    index = ChromaIndex(".data/chroma", GeminiEmbeddings(settings.api_key))
    added = index.upsert_chunks(chunks)
    print(f"Upserted {added} document chunks. Persistent collection count: {index.count()}")

if __name__ == "__main__":
    main()

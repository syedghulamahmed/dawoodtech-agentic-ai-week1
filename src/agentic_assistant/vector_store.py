"""Persistent Chroma index with Gemini-generated embeddings."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Sequence
from .documents import DocumentChunk

class ChromaIndex:
    def __init__(self, persist_directory: str | Path, embedder: Any,
                 collection_name: str = "project_documents", client: Any | None = None):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("ChromaDB missing. Run 'uv sync'.") from exc
        self.embedder = embedder
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = client or chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert_chunks(self, chunks: Sequence[DocumentChunk], batch_size: int = 32) -> int:
        if batch_size < 1:
            raise ValueError("batch_size must be positive.")
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            vectors = self.embedder.embed([item.text for item in batch], task_type="RETRIEVAL_DOCUMENT")
            self.collection.upsert(
                ids=[item.chunk_id for item in batch],
                documents=[item.text for item in batch],
                metadatas=[item.metadata for item in batch],
                embeddings=vectors,
            )
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("Search query cannot be empty.")
        if top_k < 1:
            raise ValueError("top_k must be positive.")
        count = self.collection.count()
        if count == 0:
            return []
        vector = self.embedder.embed([query], task_type="RETRIEVAL_QUERY")[0]
        result = self.collection.query(
            query_embeddings=[vector], n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [{
            "id": chunk_id,
            "document": documents[i] if i < len(documents) else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "distance": float(distances[i]) if i < len(distances) else 1.0,
            "similarity": 1.0 - float(distances[i]) if i < len(distances) else 0.0,
        } for i, chunk_id in enumerate(ids)]

    def count(self) -> int:
        return int(self.collection.count())

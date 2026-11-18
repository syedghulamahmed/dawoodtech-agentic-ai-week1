"""Gemini text embeddings with task-specific retrieval modes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class GeminiEmbeddings:
    """Adapter around the official Google Gen AI embeddings API."""

    def __init__(self, api_key: str, model: str = "gemini-embedding-001", client: Any | None = None):
        if not api_key:
            raise ValueError("An API key is required for Gemini embeddings.")
        self.model = model
        if client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError("Google Gen AI SDK missing. Run 'uv sync'.") from exc
            client = genai.Client(api_key=api_key)
        self.client = client

    def embed(self, texts: Sequence[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        clean = [text.strip() for text in texts]
        if not clean:
            return []
        if any(not text for text in clean):
            raise ValueError("Embedding input cannot contain empty text.")
        try:
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Google Gen AI SDK missing. Run 'uv sync'.") from exc
        response = self.client.models.embed_content(
            model=self.model,
            contents=clean,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        items = getattr(response, "embeddings", None) or []
        if len(items) != len(clean):
            raise RuntimeError("Gemini returned an unexpected number of embeddings.")
        vectors: list[list[float]] = []
        dimension: int | None = None
        for item in items:
            values = getattr(item, "values", None)
            if not values:
                raise RuntimeError("Gemini returned an empty embedding.")
            vector = [float(value) for value in values]
            if dimension is None:
                dimension = len(vector)
            if len(vector) != dimension:
                raise RuntimeError("Gemini returned inconsistent embedding dimensions.")
            vectors.append(vector)
        return vectors

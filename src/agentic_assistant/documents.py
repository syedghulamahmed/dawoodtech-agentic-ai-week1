"""Document loading, metadata preservation, and deterministic text chunking."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

@dataclass(frozen=True)
class DocumentPage:
    text: str
    source: str
    source_path: str
    page: int

@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    text: str
    metadata: dict[str, str | int]

def load_document(path: str | Path) -> list[DocumentPage]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{suffix}'. Use TXT, MD, PDF, or DOCX.")
    if not file_path.is_file():
        raise FileNotFoundError(f"Document not found: {file_path}")
    if suffix in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8-sig").strip()
        return [DocumentPage(text, file_path.name, str(file_path), 1)] if text else []
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF support missing. Run 'uv sync'.") from exc
        reader = PdfReader(str(file_path))
        return [
            DocumentPage(text, file_path.name, str(file_path), number)
            for number, page in enumerate(reader.pages, start=1)
            if (text := (page.extract_text() or "").strip())
        ]
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX support missing. Run 'uv sync'.") from exc
    document = Document(str(file_path))
    parts = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    text = "\n".join(parts).strip()
    return [DocumentPage(text, file_path.name, str(file_path), 1)] if text else []

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    if chunk_size < 100:
        raise ValueError("chunk_size must be at least 100 characters.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size.")
    normalized = "\n".join(line.strip() for line in text.splitlines()).strip()
    if not normalized:
        return []
    chunks, start = [], 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind("\n", start + int(chunk_size * 0.65), end)
            if boundary > start:
                end = boundary
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks

def make_chunks(pages: Iterable[DocumentPage], chunk_size: int = 900, overlap: int = 120) -> list[DocumentChunk]:
    output = []
    for page in pages:
        for index, text in enumerate(chunk_text(page.text, chunk_size, overlap)):
            identity = f"{page.source_path}|{page.page}|{index}|{text}"
            output.append(DocumentChunk(
                hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32],
                text,
                {"source": page.source, "source_path": page.source_path,
                 "page": page.page, "chunk_index": index},
            ))
    return output

def collect_document_paths(inputs: Iterable[str | Path]) -> list[Path]:
    found: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            found.update(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.add(path)
        else:
            raise FileNotFoundError(f"No supported document found at: {path}")
    return sorted(found, key=lambda item: str(item).lower())

def load_and_chunk(inputs: Iterable[str | Path], chunk_size: int = 900, overlap: int = 120) -> list[DocumentChunk]:
    pages = []
    for path in collect_document_paths(inputs):
        pages.extend(load_document(path))
    return make_chunks(pages, chunk_size, overlap)

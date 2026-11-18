"""Measure retrieval hit@5 for 500, 900 and 1400 character chunks."""
from __future__ import annotations
import csv
import chromadb
from pathlib import Path
from agentic_assistant.config import load_settings
from agentic_assistant.documents import load_and_chunk
from agentic_assistant.embeddings import GeminiEmbeddings
from agentic_assistant.vector_store import ChromaIndex

def main():
    settings=load_settings()
    with Path("eval/questions.csv").open(encoding="utf-8",newline="") as handle:
        questions=[row for row in csv.DictReader(handle) if row["expected_source"].strip()]
    embedder=GeminiEmbeddings(settings.api_key)
    measured=[]
    for size in (500,900,1400):
        overlap=max(50,size//8)
        chunks=load_and_chunk([Path("examples/docs")],chunk_size=size,overlap=overlap)
        index=ChromaIndex(".data/chroma-eval",embedder,collection_name=f"size_{size}",client=chromadb.EphemeralClient())
        index.upsert_chunks(chunks)
        hits=0
        for row in questions:
            found=index.search(row["question"],top_k=5)
            expected=row["expected_source"].strip()
            hits += int(any(item["metadata"].get("source")==expected for item in found))
        measured.append({"chunk_size":size,"overlap":overlap,"chunks":len(chunks),
                         "hits":hits,"total":len(questions),
                         "hit_rate":hits/len(questions) if questions else 0.0})
    output=Path("eval/chunk-size-results.md")
    lines=["# Measured Chunk-Size Comparison","","Live Gemini embedding retrieval hit@5; each figure is measured by this script.",
           "","| Chunk size (chars) | Overlap | Chunks | Expected-source hit@5 |",
           "|---:|---:|---:|---:|"]
    for row in measured:
        lines.append(f"| {row['chunk_size']} | {row['overlap']} | {row['chunks']} | {row['hits']}/{row['total']} ({row['hit_rate']:.1%}) |")
    output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
    print(f"Saved measured comparison to {output}")

if __name__=="__main__":
    main()

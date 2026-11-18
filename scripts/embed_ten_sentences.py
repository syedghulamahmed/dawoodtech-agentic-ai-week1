"""Embed ten sentences, find the closest pair, then persist and query them in Chroma."""
from __future__ import annotations
import math
from pathlib import Path
import chromadb
from agentic_assistant.config import load_settings
from agentic_assistant.embeddings import GeminiEmbeddings

SENTENCES = [
    "A large language model generates language as sequences of tokens.",
    "LLMs process token sequences and predict likely continuations.",
    "An embedding represents a text passage as a numeric vector.",
    "Semantic similarity compares meaning through vector representations.",
    "Chroma stores document vectors and metadata for retrieval.",
    "A persistent vector collection reloads its data after a restart.",
    "SQLite stores structured records in a relational database.",
    "A database transaction groups related changes into one operation.",
    "Conversation compaction summarizes older messages to save context.",
    "Context rot describes reduced recall as the model context grows.",
]

def cosine(a,b):
    dot=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a))
    nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

def main():
    settings=load_settings()
    embedder=GeminiEmbeddings(settings.api_key)
    vectors=embedder.embed(SENTENCES,task_type="SEMANTIC_SIMILARITY")
    pairs=[(cosine(vectors[i],vectors[j]),i,j)
           for i in range(len(vectors)) for j in range(i+1,len(vectors))]
    score,i,j=max(pairs)
    print(f"Embedded {len(vectors)} sentences; dimension={len(vectors[0])}")
    print(f"Most similar pair: cosine={score:.4f}")
    print("1.",SENTENCES[i])
    print("2.",SENTENCES[j])
    client=chromadb.PersistentClient(path=str(Path(".data")/"chroma-learning"))
    collection=client.get_or_create_collection(
        "ten_sentence_exercise",metadata={"hnsw:space":"cosine"})
    collection.upsert(
        ids=[f"sentence-{i:02d}" for i in range(len(SENTENCES))],
        documents=SENTENCES,
        metadatas=[{"source":"week2-embedding-exercise","sentence_number":i+1}
                   for i in range(len(SENTENCES))],
        embeddings=vectors,
    )
    query="Which sentence describes how text meaning is represented numerically?"
    query_vector=embedder.embed([query],task_type="SEMANTIC_SIMILARITY")[0]
    found=collection.query(query_embeddings=[query_vector],n_results=3,
                           include=["documents","metadatas","distances"])
    print("\nTop Chroma matches:")
    for doc,meta,distance in zip(found["documents"][0],found["metadatas"][0],found["distances"][0]):
        print(f"- #{meta['sentence_number']} distance={float(distance):.4f}: {doc}")

if __name__=="__main__":
    main()

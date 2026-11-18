"""Run the 20-question RAG evaluation and save actual outcomes to eval/results.csv."""
from __future__ import annotations
import csv
from pathlib import Path
from agentic_assistant.agent import build_client
from agentic_assistant.config import load_settings
from agentic_assistant.embeddings import GeminiEmbeddings
from agentic_assistant.memory import UserMemoryStore
from agentic_assistant.rag import DocumentAssistant
from agentic_assistant.vector_store import ChromaIndex

def main():
    settings=load_settings()
    index=ChromaIndex(".data/chroma",GeminiEmbeddings(settings.api_key))
    if index.count()==0:
        raise SystemExit("The Chroma index is empty. Run scripts/ingest_samples.py first.")
    store=UserMemoryStore(".data/user-memory.db")
    assistant=DocumentAssistant(build_client(settings),settings.model,index,store,
        provider=settings.provider,temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        max_history_tokens=int(__import__("os").getenv("MAX_HISTORY_TOKENS","2200")))
    with Path("eval/questions.csv").open(encoding="utf-8",newline="") as handle:
        questions=list(csv.DictReader(handle))
    results=[]
    for number,row in enumerate(questions,1):
        expected=row["expected_source"].strip()
        hits=index.search(row["question"],top_k=5)
        retrieved=[str(hit["metadata"].get("source","")) for hit in hits]
        retrieval_hit=(expected in retrieved) if expected else not bool(retrieved)
        answer=assistant.ask(row["question"],user_id="week2-eval-user")
        expected_refusal=not bool(expected)
        refusal_correct=(answer.answer.refused==expected_refusal)
        cited_sources=[source["source"] for source in answer.sources]
        row_result={
            "question":row["question"],
            "expected_source":expected,
            "retrieved_top5":";".join(retrieved),
            "retrieval_hit":str(retrieval_hit),
            "cited_sources":";".join(cited_sources),
            "refused":str(answer.answer.refused),
            "refusal_correct":str(refusal_correct),
            "result":"PASS" if retrieval_hit and refusal_correct else "REVIEW",
        }
        results.append(row_result)
        print(f"{number:02d}/{len(questions)} {row_result['result']} | hit@5={retrieval_hit} | refusal={answer.answer.refused}")
    output=Path("eval/results.csv")
    with output.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    passed=sum(item["result"]=="PASS" for item in results)
    print(f"Evaluation: {passed}/{len(results)} PASS. Results saved to {output}.")

if __name__=="__main__":
    main()

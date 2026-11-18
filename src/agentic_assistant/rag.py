"""Grounded document assistant with citations and per-user memory."""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from .context import estimate_tokens, compact_history
from .memory import UserMemoryStore

class RAGAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)
    refused: bool = False

@dataclass
class AssistantResult:
    answer: RAGAnswer
    sources: list[dict[str, Any]]
    tools_used: list[str]
    history: list[dict[str, Any]]
    compaction: dict[str, Any]
    retrieved_count: int

SYSTEM_PROMPT = """Answer only from retrieved document passages.
Return JSON: answer (string), citations (source IDs), refused (boolean).
Cite each factual answer. Never invent facts or source IDs.
If evidence is missing, refuse. Memory tools only serve the current user.
"""

class DocumentAssistant:
    def __init__(self, client: Any, model: str, vector_index: Any,
                 memory_store: UserMemoryStore, provider: str = "gemini",
                 temperature: float = 0.2, max_tokens: int = 900,
                 max_history_tokens: int = 2200, keep_recent_messages: int = 6,
                 min_similarity: float = 0.35):
        self.client, self.model = client, model
        self.index, self.memories = vector_index, memory_store
        self.provider, self.temperature, self.max_tokens = provider, temperature, max_tokens
        self.max_history_tokens, self.keep_recent_messages = max_history_tokens, keep_recent_messages
        self.min_similarity = min_similarity

    def _summarize(self, old):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role":"system","content":"Summarize older chat in at most 180 words. Preserve facts, constraints, decisions, dates and open tasks. Do not include hidden reasoning."},
                {"role":"user","content":json.dumps(list(old), ensure_ascii=False, default=str)},
            ],
            temperature=0.1, max_tokens=380,
        )
        return (response.choices[0].message.content or "").strip()

    @staticmethod
    def _parse(raw: str) -> RAGAnswer:
        raw = raw.strip()
        try:
            return RAGAnswer.model_validate_json(raw)
        except Exception:
            return RAGAnswer(answer=raw or "No grounded answer was returned.", refused=True)

    def ask(self, question: str, user_id: str = "local-user",
            history: list[dict[str, Any]] | None = None, top_k: int = 5) -> AssistantResult:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        history = [dict(item) for item in (history or [])]
        before = estimate_tokens(history)
        compaction = {"compacted":False,"before_tokens":before,
                      "after_tokens":before,"reduction_percent":0.0}
        if before > self.max_history_tokens:
            try:
                compaction = compact_history(history, self._summarize, self.keep_recent_messages)
                history = compaction["messages"]
            except Exception:
                pass

        memories = self.memories.load_for_user(user_id, limit=20)
        memory_text = "\n".join(
            "- " + item["memory_key"] + ": " + item["memory_value"][:240]
            for item in memories
        ) or "No saved memories."
        hits = [hit for hit in self.index.search(question, top_k)
                if float(hit.get("similarity",0)) >= self.min_similarity]
        sources, blocks = [], []
        for i, hit in enumerate(hits, 1):
            metadata = hit.get("metadata") or {}
            source = {"id":"S" + str(i),"chunk_id":hit.get("id",""),
                      "source":str(metadata.get("source","unknown")),
                      "page":metadata.get("page",1),
                      "chunk_index":metadata.get("chunk_index",0),
                      "similarity":round(float(hit.get("similarity",0)),4)}
            sources.append(source)
            blocks.append(
                "[" + source["id"] + "] " + source["source"] + " page " +
                str(source["page"]) + " chunk " + str(source["chunk_index"]) +
                "\n" + str(hit.get("document",""))[:3000]
            )
        system = SYSTEM_PROMPT + "\nUSER MEMORY:\n" + memory_text + "\nDOCUMENT PASSAGES:\n"
        system += "\n\n".join(blocks) if blocks else "No relevant document passages found."
        messages = [{"role":"system","content":system}, *history,
                    {"role":"user","content":question}]
        tools_used, raw = [], ""
        for unused in range(3):
            kwargs = {"model":self.model,"messages":messages,
                      "temperature":self.temperature,"max_tokens":self.max_tokens,
                      "tools":self.memories.tool_schemas()}
            if self.provider == "gemini":
                kwargs["tool_choice"] = "auto"
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            calls = getattr(message,"tool_calls",None) or []
            if not calls:
                raw = message.content or ""
                break
            if hasattr(message,"model_dump"):
                messages.append(message.model_dump(exclude_none=True))
            else:
                messages.append(message)
            for call in calls:
                name = call.function.name
                outcome = self.memories.execute_tool(
                    user_id,name,call.function.arguments or "{}")
                if name not in tools_used:
                    tools_used.append(name)
                messages.append({"role":"tool","tool_call_id":call.id,
                                 "content":json.dumps(outcome,ensure_ascii=False,default=str)})
        else:
            raw = '{"answer":"Stopped after three memory tool rounds.","citations":[],"refused":true}'
        answer = self._parse(raw)
        allowed = {item["id"] for item in sources}
        if any(item not in allowed for item in answer.citations):
            answer = RAGAnswer(answer="An unknown source was cited; refusing to guess.",refused=True)
        elif not answer.citations and not answer.refused and not tools_used:
            answer = RAGAnswer(answer="The indexed documents do not contain sufficient evidence to answer.",refused=True)
        answer = answer.model_copy(update={
            "citations":list(dict.fromkeys(item for item in answer.citations if item in allowed))
        })
        history_answer = answer.answer
        if answer.citations:
            history_answer += " Sources: " + ", ".join(answer.citations)
        updated = [*history,{"role":"user","content":question},
                   {"role":"assistant","content":history_answer}]
        return AssistantResult(answer,
            [item for item in sources if item["id"] in answer.citations],
            tools_used,updated,compaction,len(hits))

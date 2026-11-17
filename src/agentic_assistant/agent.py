"""Hand-written LLM tool-calling loop with bounded steps and validated JSON output."""
from __future__ import annotations
import json
import logging
from typing import Any
from pydantic import ValidationError
from .config import Settings
from .models import AnswerSummary
from .tools import ToolRegistry

SYSTEM_PROMPT = """You are a careful terminal assistant with access to local tools.
Choose a tool when the user's request needs current weather, exact arithmetic, or saved notes.
Never invent tool results. Use the tool result as evidence and tell the user when a tool failed.
You may call more than one tool when needed. Do not claim a tool was used unless it was called.
When complete, respond ONLY with JSON: {"answer":"...","tools_used":["..."],"confidence":0.0}
Confidence must be 0..1. No Markdown fences or extra keys. Never expose private chain-of-thought.
"""

class Agent:
    def __init__(self, client: Any, settings: Settings, tools: ToolRegistry, logger: logging.Logger | None = None):
        self.client, self.settings, self.tools = client, settings, tools
        self.logger = logger or logging.getLogger("agentic_assistant")

    def _chat(self, messages: list[dict[str, Any]], *, tools: list[dict[str, Any]] | None = None) -> Any:
        kwargs = {"model": self.settings.model, "messages": messages, "temperature": self.settings.temperature, "max_tokens": self.settings.max_tokens}
        if tools is not None:
            kwargs["tools"] = tools
            if self.settings.provider == "gemini":
                kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)

    @staticmethod
    def _message_dict(message: Any) -> dict[str, Any]:
        if hasattr(message, "model_dump"):
            return message.model_dump(exclude_none=True)
        if isinstance(message, dict):
            return message
        raise TypeError("Unsupported assistant message object returned by provider.")

    @staticmethod
    def _extract_json(text: str) -> AnswerSummary:
        raw = text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        try:
            return AnswerSummary.model_validate_json(raw)
        except ValidationError:
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                raise
            return AnswerSummary.model_validate_json(raw[start:end + 1])

    def run(self, user_request: str) -> AnswerSummary:
        if not user_request.strip():
            raise ValueError("Please enter a non-empty request.")
        messages = [{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user_request.strip()}]
        tools_used: list[str] = []
        for step in range(1, self.settings.max_agent_steps + 1):
            self.logger.info("agent_step=%s", step)
            response = self._chat(messages, tools=self.tools.openai_schemas())
            message = response.choices[0].message
            calls = getattr(message, "tool_calls", None) or []
            if calls:
                messages.append(self._message_dict(message))
                for call in calls:
                    name, arguments = call.function.name, call.function.arguments or "{}"
                    self.logger.info("tool_call name=%s", name)
                    result = self.tools.execute(name, arguments)
                    if name in {tool.name for tool in self.tools.definitions} and name not in tools_used:
                        tools_used.append(name)
                    messages.append({"role":"tool","tool_call_id":call.id,"content":json.dumps(result,ensure_ascii=False,default=str)})
                continue
            final_text = message.content or ""
            try:
                summary = self._extract_json(final_text)
            except ValidationError:
                self.logger.warning("final_json_invalid; requesting_repair")
                repair = [{"role":"system","content":"Convert supplied content into JSON with exactly answer (string), tools_used (string array), confidence (0..1 number). JSON only; add no facts."},{"role":"user","content":final_text or "No final response."}]
                repaired = self._chat(repair, tools=None).choices[0].message.content or ""
                try:
                    summary = self._extract_json(repaired)
                except ValidationError:
                    summary = AnswerSummary(answer=final_text.strip() or "The model did not return valid structured output.",tools_used=tools_used,confidence=0.2)
            return summary.model_copy(update={"tools_used":tools_used})
        self.logger.warning("max_agent_steps_reached limit=%s",self.settings.max_agent_steps)
        return AnswerSummary(answer=f"Stopped after {self.settings.max_agent_steps} model steps to prevent an unbounded loop.",tools_used=tools_used,confidence=0.25)

def build_client(settings: Settings):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK missing. Run uv sync.") from exc
    return OpenAI(api_key=settings.api_key,base_url=settings.base_url,timeout=settings.timeout_seconds,max_retries=4)

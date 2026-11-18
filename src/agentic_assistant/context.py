"""Conversation token estimation and high-fidelity history compaction."""
from __future__ import annotations
import json
import re
from collections.abc import Callable, Sequence
from typing import Any

def estimate_tokens(messages: Sequence[dict[str, Any]]) -> int:
    serialized = json.dumps(messages, ensure_ascii=False, default=str)
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(serialized))
    except ImportError:
        return max(1, (len(re.findall(r"\w+|[^\w\s]", serialized)) * 4) // 3)

def compact_history(messages: Sequence[dict[str, Any]],
                    summarizer: Callable[[Sequence[dict[str, Any]]], str],
                    keep_recent_messages: int = 6) -> dict[str, Any]:
    if keep_recent_messages < 2:
        raise ValueError("Keep at least two recent messages to preserve a complete turn.")
    original = [dict(message) for message in messages]
    before = estimate_tokens(original)
    if len(original) <= keep_recent_messages:
        return {"messages": original, "compacted": False, "before_tokens": before,
                "after_tokens": before, "reduction_percent": 0.0}
    older, recent = original[:-keep_recent_messages], original[-keep_recent_messages:]
    summary = summarizer(older).strip()
    if not summary:
        raise ValueError("The history summarizer returned an empty summary.")
    compacted = [{
        "role": "system",
        "content": "Compressed prior conversation. Preserve facts, decisions, constraints, and open tasks:\n" + summary[:5000],
    }, *recent]
    after = estimate_tokens(compacted)
    reduction = max(0.0, (before - after) / before * 100) if before else 0.0
    return {"messages": compacted, "compacted": True, "before_tokens": before,
            "after_tokens": after, "reduction_percent": round(reduction, 1)}

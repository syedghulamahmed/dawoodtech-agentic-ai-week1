"""Deterministic offline provider; it never contacts an external model."""
from __future__ import annotations
import json
from types import SimpleNamespace
from uuid import uuid4

class _FakeMessage:
    def __init__(self,content=None,tool_calls=None): self.content=content; self.tool_calls=tool_calls or []
    def model_dump(self,exclude_none=True):
        result={"role":"assistant"}
        if self.content is not None: result["content"]=self.content
        if self.tool_calls:
            result["tool_calls"]=[{"id":c.id,"type":"function","function":{"name":c.function.name,"arguments":c.function.arguments}} for c in self.tool_calls]
        return result

class _FakeCompletions:
    def create(self,**kwargs):
        messages=kwargs["messages"]
        user=next(m["content"] for m in reversed(messages) if m["role"]=="user")
        tool_msgs=[m for m in messages if m["role"]=="tool"]
        assistant_msgs=[m for m in messages if m.get("tool_calls")]
        if tool_msgs:
            names=[]
            for m in assistant_msgs:
                for c in m["tool_calls"]:
                    name=c.get("function",{}).get("name")
                    if name and name not in names: names.append(name)
            observed=json.loads(tool_msgs[-1]["content"])
            content=json.dumps({"answer":"Offline demonstration completed. Tool observation: "+json.dumps(observed,ensure_ascii=False),"tools_used":names,"confidence":0.8},ensure_ascii=False)
            return SimpleNamespace(choices=[SimpleNamespace(message=_FakeMessage(content=content))])
        low=user.lower()
        if any(w in low for w in ("calculate","compute","arithmetic")): name,args="calculate",{"expression":"24 * 19 + 3"}
        elif any(w in low for w in ("find","search")): name,args="search_notes",{"query":"Week 1 agent loop"}
        else: name,args="save_note",{"title":"Demo reminder","content":"The Week 1 agent loop uses tool calls."}
        call=SimpleNamespace(id="call_"+uuid4().hex[:10],type="function",function=SimpleNamespace(name=name,arguments=json.dumps(args)))
        return SimpleNamespace(choices=[SimpleNamespace(message=_FakeMessage(tool_calls=[call]))])

class MockLLMClient:
    """Matches the client surface used by Agent; no API/network access."""
    def __init__(self): self.chat=SimpleNamespace(completions=_FakeCompletions())

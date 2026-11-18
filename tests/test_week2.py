from types import SimpleNamespace
from agentic_assistant.context import compact_history, estimate_tokens
from agentic_assistant.documents import DocumentPage, chunk_text, make_chunks
from agentic_assistant.memory import UserMemoryStore
from agentic_assistant.rag import DocumentAssistant

def test_chunking_is_bounded_and_overlapping():
    text = "\n\n".join(f"Paragraph {i}: " + ("context " * 40) for i in range(12))
    chunks = chunk_text(text, chunk_size=300, overlap=40)
    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 300 for chunk in chunks)
    assert chunks[0] != chunks[1]

def test_chunking_validates_limits():
    try:
        chunk_text("some text", chunk_size=99)
    except ValueError:
        pass
    else:
        raise AssertionError("Too-small chunk size was accepted")
    try:
        chunk_text("some text", chunk_size=100, overlap=100)
    except ValueError:
        pass
    else:
        raise AssertionError("Overlap equal to chunk size was accepted")

def test_metadata_and_chunk_ids_are_stable():
    page = DocumentPage("Source passage. " * 40, "guide.md", "docs/guide.md", 3)
    first = make_chunks([page], chunk_size=160, overlap=20)
    second = make_chunks([page], chunk_size=160, overlap=20)
    assert first
    assert first[0].metadata["source"] == "guide.md"
    assert first[0].metadata["page"] == 3
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]

def test_memory_isolated_per_user_and_upserted(tmp_path):
    store = UserMemoryStore(tmp_path / "memory.db")
    store.save("user-a", "format", "Concise bullets")
    store.save("user-a", "format", "Short structured answers")
    store.save("user-b", "format", "Detailed paragraphs")
    assert store.load_for_user("user-a")[0]["memory_value"] == "Short structured answers"
    assert store.load_for_user("user-b")[0]["memory_value"] == "Detailed paragraphs"
    assert store.search("user-a", "structured")["count"] == 1
    assert store.forget("user-a", "format")["deleted"] is True
    assert store.load_for_user("user-a") == []
    assert len(store.load_for_user("user-b")) == 1

def test_memory_schema_does_not_expose_user_id(tmp_path):
    store = UserMemoryStore(tmp_path / "memory.db")
    schema = next(item for item in store.tool_schemas()
                  if item["function"]["name"] == "save_memory")
    assert set(schema["function"]["parameters"]["properties"]) == {"key", "value"}

def test_compaction_summarizes_older_and_keeps_recent():
    history = []
    for i in range(12):
        history += [
            {"role":"user", "content":f"Question {i}: " + ("detail " * 40)},
            {"role":"assistant", "content":f"Answer {i}: " + ("result " * 40)},
        ]
    compacted = compact_history(
        history,
        lambda old: "Project is a document assistant. User needs evidence citations.",
        keep_recent_messages=4,
    )
    assert compacted["compacted"]
    assert len(compacted["messages"]) == 5
    assert compacted["after_tokens"] < compacted["before_tokens"]
    assert compacted["messages"][-1]["content"] == history[-1]["content"]
    assert estimate_tokens(compacted["messages"]) == compacted["after_tokens"]

class FakeIndex:
    def search(self, query, top_k=5):
        return [{
            "id":"chunk-1",
            "document":"An agent observes tool output before deciding what to do next.",
            "metadata":{"source":"agent-loop.md","page":2,"chunk_index":0},
            "distance":0.12,"similarity":0.88,
        }]

class FakeCompletions:
    def __init__(self, content):
        self.content, self.calls = content, []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content=self.content, tool_calls=[])
        )])

def make_assistant(tmp_path, content):
    store = UserMemoryStore(tmp_path / "memory.db")
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(content)))
    return DocumentAssistant(client, "fake-model", FakeIndex(), store), store, client

def test_rag_formats_empty_json_refusal_as_readable_message(tmp_path):
    assistant, _, _ = make_assistant(
        tmp_path,
        '{"answer":"","citations":[],"refused":true}',
    )
    result = assistant.ask("What is the population of Tokyo?", user_id="student-1")
    assert result.answer.refused is True
    assert result.answer.citations == []
    assert "sufficient evidence" in result.answer.answer.lower()
    assert not result.answer.answer.lstrip().startswith("{")

def test_rag_validates_known_citations(tmp_path):
    assistant, _, _ = make_assistant(
        tmp_path,
        '{"answer":"The agent observes tool output.","citations":["S1"],"refused":false}',
    )
    result = assistant.ask("Explain the agent loop.", user_id="student-1")
    assert result.answer.refused is False
    assert result.answer.citations == ["S1"]
    assert result.sources[0]["source"] == "agent-loop.md"

def test_rag_refuses_unknown_citation(tmp_path):
    assistant, _, _ = make_assistant(
        tmp_path,
        '{"answer":"Unsupported claim.","citations":["S99"],"refused":false}',
    )
    result = assistant.ask("Explain the agent loop.", user_id="student-1")
    assert result.answer.refused is True
    assert result.answer.citations == []

def test_rag_refuses_unsupported_answer_without_citation(tmp_path):
    assistant, _, _ = make_assistant(
        tmp_path,
        '{"answer":"The system has 99 customers.","citations":[],"refused":false}',
    )
    result = assistant.ask("How many customers?", user_id="student-1")
    assert result.answer.refused is True

def test_memory_for_one_user_is_loaded_only_for_that_user(tmp_path):
    assistant, store, client = make_assistant(
        tmp_path,
        '{"answer":"The retrieved document explains it.","citations":["S1"],"refused":false}',
    )
    store.save("student-a", "preferred_style", "Concise technical explanations")
    assistant.ask("Explain the loop.", user_id="student-a")
    prompt = client.chat.completions.calls[0]["messages"][0]["content"]
    assert "Concise technical explanations" in prompt
    assistant.ask("Explain the loop.", user_id="student-b")
    second_prompt = client.chat.completions.calls[1]["messages"][0]["content"]
    assert "Concise technical explanations" not in second_prompt

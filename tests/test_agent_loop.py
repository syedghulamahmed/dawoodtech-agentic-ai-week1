from types import SimpleNamespace
from agentic_assistant.agent import Agent
from agentic_assistant.cli import load_settings_for_demo
from agentic_assistant.mock_provider import MockLLMClient
from agentic_assistant.tools import build_registry

def settings_for(tmp_path,**overrides):
    base=load_settings_for_demo()
    values={name:getattr(base,name) for name in ("provider","api_key","base_url","model","temperature","max_tokens","timeout_seconds","max_agent_steps")}
    values.update(sqlite_path=tmp_path/"notes.db",log_path=tmp_path/"agent.log"); values.update(overrides)
    return base.__class__(**values)

def test_agent_loop_calculator_and_valid_summary(tmp_path):
    settings=settings_for(tmp_path); agent=Agent(MockLLMClient(),settings,build_registry(settings.sqlite_path))
    result=agent.run("Calculate 24 times 19 plus 3.")
    assert result.tools_used==["calculate"] and result.confidence==0.8 and "459" in result.answer

def test_agent_saves_then_finds_note(tmp_path):
    settings=settings_for(tmp_path); registry=build_registry(settings.sqlite_path); agent=Agent(MockLLMClient(),settings,registry)
    assert agent.run("Remember the Week 1 agent loop.").tools_used==["save_note"]
    found=agent.run("Find my note about the Week 1 agent loop.")
    assert found.tools_used==["search_notes"] and "Week 1" in found.answer

def test_agent_stops_at_step_limit(tmp_path):
    class Endless:
        def create(self,**kwargs):
            call=SimpleNamespace(id="call_limit",function=SimpleNamespace(name="calculate",arguments='{"expression":"1 + 1"}'))
            message=SimpleNamespace(content=None,tool_calls=[call],model_dump=lambda exclude_none=True:{"role":"assistant","tool_calls":[{"id":"call_limit","type":"function","function":{"name":"calculate","arguments":'{"expression":"1 + 1"}'}}]})
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
    settings=settings_for(tmp_path,max_agent_steps=1); client=SimpleNamespace(chat=SimpleNamespace(completions=Endless()))
    result=Agent(client,settings,build_registry(settings.sqlite_path)).run("Calculate 1 + 1")
    assert result.tools_used==["calculate"] and "Stopped after 1" in result.answer

def test_ollama_omits_tool_choice(tmp_path):
    class Recorder:
        kwargs=None
        def create(self,**kwargs):
            self.kwargs=kwargs
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"answer":"ok","tools_used":[],"confidence":0.8}',tool_calls=[]))])
    settings=settings_for(tmp_path,provider="ollama")
    recorder=Recorder(); agent=Agent(SimpleNamespace(chat=SimpleNamespace(completions=recorder)),settings,build_registry(settings.sqlite_path))
    agent._chat([{"role":"user","content":"test"}],tools=agent.tools.openai_schemas())
    assert "tools" in recorder.kwargs and "tool_choice" not in recorder.kwargs

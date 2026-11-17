from agentic_assistant.agent import build_client
from agentic_assistant.cli import load_settings_for_demo


def test_build_client_retries_transient_errors(monkeypatch):
    captured = {}

    def fake_openai(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("openai.OpenAI", fake_openai)
    settings = load_settings_for_demo()

    build_client(settings)

    assert captured["max_retries"] == 4
    assert captured["timeout"] == settings.timeout_seconds
    assert captured["api_key"] == settings.api_key

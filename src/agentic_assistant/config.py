"""Environment-based provider configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    provider: str
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    max_agent_steps: int
    sqlite_path: Path
    log_path: Path


def load_settings() -> Settings:
    """Load settings from .env and process environment variables."""
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

    if provider not in {"gemini", "ollama"}:
        raise ValueError("LLM_PROVIDER must be either 'gemini' or 'ollama'.")

    if provider == "gemini":
        base_url = os.getenv(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ).strip()
        model = os.getenv("LLM_MODEL", "gemini-3.8-flash").strip()
        api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        ).strip()
        if not api_key or api_key == "replace_with_your_gemini_api_key":
            raise ValueError(
                "Gemini API key missing. Add LLM_API_KEY to your .env file."
            )
    else:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip()
        model = os.getenv("LLM_MODEL", "qwen3:4b").strip()
        api_key = (os.getenv("LLM_API_KEY") or "ollama").strip()

    try:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "900"))
        timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
        max_agent_steps = int(os.getenv("MAX_AGENT_STEPS", "6"))
    except ValueError as exc:
        raise ValueError("Numeric environment settings contain an invalid value.") from exc

    if not 0 <= temperature <= 2:
        raise ValueError("LLM_TEMPERATURE must be between 0 and 2.")
    if max_tokens < 100:
        raise ValueError("LLM_MAX_TOKENS must be at least 100.")
    if timeout_seconds <= 0:
        raise ValueError("REQUEST_TIMEOUT_SECONDS must be positive.")
    if max_agent_steps < 1:
        raise ValueError("MAX_AGENT_STEPS must be at least 1.")

    return Settings(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
        max_agent_steps=max_agent_steps,
        sqlite_path=Path(os.getenv("SQLITE_PATH", ".data/notes.db")),
        log_path=Path(os.getenv("LOG_PATH", "logs/agent.log")),
    )
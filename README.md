# Tool-Using Assistant — DawoodTech Agentic AI, Week 1

A Python terminal assistant with a hand-written LLM agent loop, Gemini/Ollama provider configuration, Open-Meteo weather, safe calculator, SQLite notes, and Pydantic-validated JSON summaries.

> The repository intentionally contains no API keys. Configure credentials locally in `.env`; never commit that file.

See the project source, tests, and docs for setup and implementation details. Run `uv sync --extra dev` then `uv run pytest`. Start with `uv run agentic-assistant` after configuring a provider.

**Evidence note:** Mock/offline tests validate application logic. They are not evidence of live Gemini inference. Live evaluation and demo artifacts must be generated with a real provider before submission.
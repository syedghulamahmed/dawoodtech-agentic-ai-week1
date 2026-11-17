"""Interactive command-line interface."""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from .agent import Agent, build_client
from .config import load_settings
from .mock_provider import MockLLMClient
from .tools import build_registry

def configure_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger("agentic_assistant"); logger.setLevel(logging.INFO); logger.handlers.clear()
    formatter=logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for handler in (logging.FileHandler(log_path,encoding="utf-8"),logging.StreamHandler()):
        handler.setFormatter(formatter); logger.addHandler(handler)
    return logger

def load_settings_for_demo():
    from .config import Settings
    return Settings(provider="mock",api_key="offline",base_url="offline://mock",model="offline-demo-model",temperature=0.0,max_tokens=500,timeout_seconds=5,max_agent_steps=4,sqlite_path=Path(".data/demo-notes.db"),log_path=Path("logs/demo_runs.log"))

def run_demo() -> int:
    settings=load_settings_for_demo(); logger=configure_logging(settings.log_path)
    agent=Agent(MockLLMClient(),settings,build_registry(settings.sqlite_path),logger)
    examples=["Calculate 24 times 19 plus 3.","Remember that the Week 1 agent loop uses tool calls.","Find my note about the Week 1 agent loop."]
    print("OFFLINE DEMO — deterministic mock model; not a live Gemini/Ollama run.\n")
    for index,prompt in enumerate(examples,1):
        result=agent.run(prompt); print(f"RUN {index}: {prompt}"); print(result.model_dump_json(indent=2)); print()
    return 0

def main() -> int:
    parser=argparse.ArgumentParser(description="Tool-using terminal assistant (Gemini/Ollama).")
    parser.add_argument("--demo",action="store_true",help="Run offline mock demonstrations; no live LLM.")
    args=parser.parse_args()
    if args.demo: return run_demo()
    try:
        settings=load_settings(); logger=configure_logging(settings.log_path)
        agent=Agent(build_client(settings),settings,build_registry(settings.sqlite_path),logger)
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    print(f"Agentic assistant ready | provider={settings.provider} | model={settings.model}")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        try: prompt=input("\nYou: ").strip()
        except (EOFError,KeyboardInterrupt):
            print("\nGoodbye."); return 0
        if prompt.lower() in {"exit","quit"}: print("Goodbye."); return 0
        if not prompt: continue
        try: print(agent.run(prompt).model_dump_json(indent=2))
        except Exception as exc:
            logger.exception("request_failed"); print(f"Request failed: {type(exc).__name__}: {exc}")

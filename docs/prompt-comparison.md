# Prompt comparison task

The script scripts/compare_prompts.py sends the same user request to a configured live provider under three system prompts: a basic assistant role; a tutor role with audience and brevity constraints; and a tutor role with explicit structure and an example.

Run after provider setup:

```bash
uv run python scripts/compare_prompts.py
```

It writes actual responses to docs/prompt-comparison-results.md. Review the outputs and complete the observation table yourself. Do not invent results before running the live provider.

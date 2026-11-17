# Gemini and Ollama compatibility notes

The project uses the OpenAI Python SDK with Google's Gemini-compatible endpoint:

https://generativelanguage.googleapis.com/v1beta/openai/

The base URL, model, and key are configurable through environment variables. The default Gemini model is `gemini-3.5-flash-lite`, a stable, cost-efficient model intended for high-volume agentic tasks. The client retries transient errors up to four times. A 503 `UNAVAILABLE` response indicates temporary service overload; retry with backoff and, if needed, switch to another stable model. The OpenAI client retries transient errors up to four times with the SDK's retry/backoff behavior. A persistent HTTP 503 is a provider-capacity issue; retries cannot guarantee availability, so temporarily try another stable model such as `gemini-3.5-flash-lite`. The code uses chat completions, messages, JSON-schema function tools, and tool-call IDs. Gemini requests set tool_choice to auto. The application executes tool calls in Python and sends observations back with the matching call ID.

Ollama is supported through its OpenAI-compatible local endpoint. The implementation omits tool_choice for Ollama because its compatibility table does not list that field.

References:
- https://ai.google.dev/gemini-api/docs/openai
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/function-calling
- https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx
- https://ollama.com/library/qwen3

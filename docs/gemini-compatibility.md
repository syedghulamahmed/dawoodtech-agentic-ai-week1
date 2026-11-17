# Gemini and Ollama compatibility notes

## Gemini OpenAI-compatible endpoint

Google documents this OpenAI-compatible base URL:

`https://generativelanguage.googleapis.com/v1beta/openai/`

The Python OpenAI client can call Gemini chat completions by supplying a Gemini API key, this base URL, and a compatible Gemini model.

Google's compatibility examples explicitly demonstrate these chat-completion features:

- `model` and `messages` for selecting the model and passing the conversation.
- `tools` and `tool_choice="auto"` for function calling.
- `stream=True` for streamed responses.
- `reasoning_effort` on supported models, mapped by Google to Gemini thinking levels or budgets.
- Gemini-specific `thinking_config` and other features through `extra_body`.
- Structured JSON output using the OpenAI SDK parsing / response-format pattern.
- Multimodal image and audio input in message content.
- `service_tier` for documented Flex and Priority inference.

The working Week 1 assistant actually sent and successfully used `model`, `messages`, `temperature`, `max_tokens`, `tools`, and `tool_choice="auto"` with `gemini-3.5-flash-lite`. This describes the tested subset; it is not a guarantee that every OpenAI parameter is supported by every Gemini model. Check current Google documentation before adding optional parameters.

The actual project base URL, model, temperature, max token limit, and key are configurable using environment variables. The OpenAI SDK is configured to retry transient errors up to four times. Retries cannot guarantee success during a prolonged 503 service-capacity incident.

## Ollama

Ollama is supported through its local OpenAI-compatible endpoint:

`http://localhost:11434/v1`

The project omits `tool_choice` for Ollama because the compatibility table used by the project does not list that field. Configure `LLM_PROVIDER=ollama`, a local model name, and keep the Ollama server running.

## References

- Google, OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google, Function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Google, Models: https://ai.google.dev/gemini-api/docs/models
- Ollama, OpenAI compatibility: https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx
- Ollama, Qwen 3 model library: https://ollama.com/library/qwen3

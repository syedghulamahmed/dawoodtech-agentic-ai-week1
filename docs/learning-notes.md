# Week 1 Learning Notes — LLM Foundations and the Agent Loop

## LLMs, tokens, and context

A large language model (LLM) is a neural network trained on large collections of data to process and generate language as token sequences. A token can represent a whole word, part of a word, punctuation, or another piece of text. The model does not necessarily receive text as one token per word; the tokenizer converts the input into tokens.

The context window is the amount of tokenized information the model can consider in a request, including instructions, conversation messages, tool descriptions, and tool results. A larger context window can hold more information, but irrelevant history still consumes context. Temperature affects how varied or predictable generated responses are: a lower value generally makes responses more consistent, while a higher value makes them more varied. The maximum-output-token setting limits how much text the model can generate in one response.

## Messages and API calls

The project sends a chat-completion messages array. The system message defines the assistant's role and rules; the user message contains the task; assistant messages can contain text or tool-call requests; and tool messages return the result of a function. A tool result is associated with the matching tool-call ID so the model can connect the observation to the request it made.

## Workflows versus agents — reading summary

A workflow and an agent both use language models and may use tools, but they differ in who controls the sequence of steps. In a workflow, the developer decides the path in advance. The application might classify a request, send it to a particular prompt, pass the response to another step, and validate the result. The same sequence is followed for each request unless the code explicitly branches. This makes workflows useful when a task can be divided into known subtasks and a predictable process is important. Examples include drafting content and then translating it, or preparing an outline and then checking it before writing the full document.

An agent has more control over deciding what to do next. After receiving the user's request and the available tools, the model can select a tool, inspect its result, and decide whether another action is needed. The next step is therefore influenced by observations rather than being entirely fixed in advance. This is useful for open-ended tasks where the number or order of actions cannot be reliably predicted, such as investigating a coding problem or gathering information from several sources.

This flexibility has costs. Each additional model call can increase latency and API usage, and an incorrect choice can affect later steps. Tool outputs must be checked, permissions must be controlled, and the application needs stopping conditions and error handling. The practical design lesson is to start with the simplest approach: use a workflow when the steps are known, and introduce an agent loop only when model-driven decisions add useful flexibility. This project uses an agent loop because the model must decide whether weather, calculation, or note tools are needed and can request more than one tool before producing its final answer.

Source: Anthropic, “Building effective agents” — https://www.anthropic.com/engineering/building-effective-agents

## Gemini OpenAI compatibility — documented features and project usage

Google documents an OpenAI-compatible endpoint at:

`https://generativelanguage.googleapis.com/v1beta/openai/`

The Python OpenAI client can be reused by setting the Gemini API key, changing the client's base URL, and selecting a compatible Gemini model. Google's examples show chat completions with a `model` and `messages` array. The documented examples also demonstrate:

- `tools` with function definitions and `tool_choice="auto"` for function calling.
- `stream=True` for streamed chat-completion responses.
- `reasoning_effort` for supported Gemini thinking models; Google maps this to model-specific thinking levels or budgets.
- Gemini-specific options such as `thinking_config` through `extra_body`.
- Structured JSON output through the OpenAI client's parsing / `response_format` pattern.
- Multimodal message content examples for image and audio input.
- `service_tier` values such as `priority` and `flex` for the corresponding inference tiers.

For this project, the actual successful Gemini 3.5 Flash-Lite requests used `model`, `messages`, `temperature`, `max_tokens`, `tools`, and `tool_choice="auto"`. This is the subset exercised by the working assistant, not a claim that every OpenAI parameter is accepted by every Gemini model. Optional parameter support can vary by endpoint and model, so check Google's current compatibility documentation before adding another parameter.

Sources:
- Google, “OpenAI compatibility” — https://ai.google.dev/gemini-api/docs/openai
- Google, “Function calling” — https://ai.google.dev/gemini-api/docs/function-calling

## ReAct: reason, act, observe

ReAct combines reasoning traces with actions that interact with an external environment. In my own words, the loop works like this: first the model considers what the request requires and chooses a useful next step (reason); then it requests an action such as a tool call (act); Python executes that function and returns the real result (observe). The model uses the observation to decide whether it has enough information or needs another action. This cycle continues until it can provide a final answer or the application reaches a stop condition.

Figure 1 of the ReAct paper contrasts standard prompting, reasoning-only, acting-only, and ReAct. It illustrates that reasoning without external feedback can remain disconnected from the environment, while actions without useful reasoning can repeat unsuitable actions. ReAct interleaves thoughts, actions, and observations so the model can use external results, update its plan, and respond to unexpected results. In this implementation, the visible and testable parts are the model's tool requests, Python execution, tool observations, and final response; the application does not print private chain-of-thought.

Source: Yao et al., “ReAct: Synergizing Reasoning and Acting in Language Models” — https://arxiv.org/abs/2210.03629

## Tool calling and structured output

A tool schema describes a function's name, purpose, and JSON parameters. The model requests a tool; the application validates the arguments and executes the function. Tool-call IDs connect each request to its result. Pydantic validates tool arguments and the final `AnswerSummary`: `answer` (string), `tools_used` (array), and `confidence` (number from 0 to 1). The application derives `tools_used` from functions actually executed rather than trusting the model to list tools.

## Reliability controls

- A maximum agent-step limit prevents an unbounded loop.
- Tool arguments are validated before execution.
- The calculator parses a restricted AST and never uses `eval()`.
- SQLite queries use bound parameters.
- Network calls have timeouts.
- Final JSON is parsed and validated with Pydantic.
- API keys and local data stay out of version control.

## References

- Anthropic, Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Google, Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google, Gemini function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Yao et al., ReAct: https://arxiv.org/abs/2210.03629

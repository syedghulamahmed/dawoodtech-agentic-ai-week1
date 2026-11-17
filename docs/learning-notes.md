# Week 1 Learning Notes — LLM Foundations and the Agent Loop

## LLMs, tokens, and context
A large language model is a neural network trained on large datasets to predict and generate token sequences. Tokens may be words, word fragments, punctuation, or other text units. A context window is the amount of tokenized input and conversation history the model can consider. Temperature influences output variation; max output tokens limits generated length.

## Messages and API calls
Chat-completion requests commonly use a messages array. A system message sets behavior, a user message provides the request, and assistant messages contain responses or tool calls. After Python executes a requested function, the result is returned in a tool message linked by tool-call ID.

## Workflows versus agents
A workflow follows a path selected in advance by the developer. An agent gives the model more control over choosing tools or next actions based on the request and observations. The application still validates arguments, executes functions, manages permissions, handles errors, and sets stopping rules. Agents are useful when the required sequence cannot be fully predicted, but can increase latency, cost, and error propagation. Start with the simplest effective design.

## ReAct: reason, act, observe
The ReAct pattern combines model reasoning with actions in an external environment. The model identifies what information or action is needed (reason), selects a function such as a search or calculator (act), and receives the executed result (observe). It then uses that observation to decide what to do next. This cycle repeats until a final response or stop condition.

## Tool calling and structured output
A tool schema describes a function name, purpose, and JSON parameters. The model requests a tool; the application validates and executes it. Tool-call IDs connect each request to its result. Pydantic validates tool arguments and the final AnswerSummary: answer (string), tools_used (array), and confidence (0–1). The application derives tools_used from functions actually executed.

## Reliability controls
- Maximum agent steps prevent an unbounded loop.
- Tool arguments are validated before execution.
- The calculator parses a restricted AST and never uses eval().
- SQLite queries use bound parameters.
- Network calls have timeouts.
- Final JSON is parsed and validated.
- API keys and local data stay out of version control.

## References
- Anthropic, Building effective agents: https://www.anthropic.com/research/building-effective-agents
- Yao et al., ReAct: https://arxiv.org/abs/2210.03629
- Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Gemini function calling: https://ai.google.dev/gemini-api/docs/function-calling

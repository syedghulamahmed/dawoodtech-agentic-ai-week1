# Context Engineering and Conversation Compaction

A model context includes system instructions, user messages, assistant messages, tool descriptions, tool results, retrieved documents, and other information sent with the request. The context window is a finite token budget. More context is not automatically better because irrelevant, repeated, or noisy content competes with information needed for the current task.

Context rot describes reduced ability to accurately retrieve information as context grows. Models can lose focus or become less accurate over long inputs even before the hard context limit is reached. Context engineering therefore chooses the smallest high-signal context that supports the task.

A useful strategy is to retain recent conversation turns verbatim and summarize older turns into a compact note containing user goals, relevant facts, decisions, constraints, dates, and unresolved tasks. Do not summarize tool-call messages in a way that breaks the relationship between a tool call and its result.

This project estimates tokens with the cl100k_base tokenizer when available. If the tokenizer package is absent, it uses a documented rough estimate. The compaction report records before and after counts and percentage reduction; the estimate is not the provider's authoritative billable token count.

Retrieval is another context-management technique: instead of inserting every document into every prompt, retrieve a few relevant passages for the current question and include their source metadata.

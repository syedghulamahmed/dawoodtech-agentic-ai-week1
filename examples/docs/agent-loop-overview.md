# Agent Loop Foundations

An agent loop lets a language model decide which action to take next, observe the result, and continue until the task is complete. A typical cycle has three parts: reason about the immediate next step, act by requesting a tool, and observe the tool result. The model can then decide whether another tool is required or whether it has enough evidence to answer.

A tool call is not direct code execution by the model. The application receives a named function and JSON arguments, validates the arguments, executes the local function, and returns the result with the matching tool-call ID. The model sees that observation on its next turn.

A safe agent needs a maximum step count, strict argument validation, error handling, network timeouts, and a clear stop condition. Tool usage should be recorded by the application after execution, rather than trusting the model to claim what it used.

The Week 1 terminal assistant has weather, calculator, and SQLite note tools. It uses Pydantic schemas and a hand-written loop. It supports Gemini and Ollama-compatible chat endpoints.

# Long-Term Memory and Data Isolation

Long-term memory stores concise facts that should remain available across sessions, such as a user's preferred response format or an explicitly saved project preference. It should not automatically store every conversation message. Memory is most useful when each entry has a short key, a bounded value, and a clear purpose.

This project stores memories in SQLite with a composite unique key of user_id and memory_key. Saving the same key for the same user updates that value. Loading, searching, and deleting always filter by the current user ID.

The user ID is an application-controlled value. It is not included in the model-facing function schema and cannot be supplied by an LLM tool call. A web application must bind this ID to an authenticated account on the server. A text field is acceptable only for a local single-user demonstration and is not authentication.

The user should explicitly request that a personal fact be remembered. Memory should be inspectable and deletable. Avoid storing passwords, API keys, payment data, or other secrets. Use a pseudonymous internal user identifier instead of an email address or a public personal identifier.

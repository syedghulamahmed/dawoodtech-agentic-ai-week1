# Designing Effective Agent Tools

A good agent tool has one narrow purpose, an explicit name, an accurate description, strict inputs, and compact outputs. Avoid several overlapping tools that do nearly the same thing; ambiguous choices make it harder for the model to select the right action.

Tool names should communicate an action and resource, such as search_memory or get_weather. Descriptions should state what the tool does, when it should be used, important limitations, and what the result contains. Input schemas should use meaningful parameter names, required fields, sensible length limits, and validation.

Tool output should be concise and high-signal. Large datasets should be filtered, paginated, or summarized. Return actionable error objects that tell the model what input was invalid without exposing stack traces, credentials, or internal filesystem details.

Every tool should have an evaluation set that measures correct selection, argument quality, output usefulness, and error recovery. Tests should include normal, boundary, missing-data, and invalid-input cases.

The memory tools in Week 2 are save_memory, search_memory, and forget_memory. The application supplies the current user's ID outside the model-facing schema, preventing the model from selecting a different user's record.

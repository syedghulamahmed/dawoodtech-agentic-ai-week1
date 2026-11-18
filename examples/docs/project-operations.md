# Week 2 Project Operations and Evaluation

The Week 2 application extends the Week 1 Python assistant. The Streamlit interface lets a user upload PDF, DOCX, TXT, and Markdown documents, inspect the number of indexed chunks, save memories, ask document questions, and see source citations or an explicit refusal.

The sample knowledge base is stored in examples/docs. The default chunking configuration is 900 characters with 120 characters of overlap. The vector index is persisted under .data/chroma and the memory database is stored under .data/user-memory.db. These paths are local runtime data and must not be committed to source control.

The evaluation file eval/questions.csv contains answerable and unanswerable questions. Each answerable question specifies an expected source filename. An unanswerable question has no expected source and should be refused. Evaluation should report retrieval hit@5 and whether the result was refused as expected.

To compare chunk settings, run scripts/compare_chunk_sizes.py. It tests 500, 900, and 1400 character chunks and reports whether the expected source appears in the top five results. The result table should be generated from an actual live embedding run, not filled with guessed values.

A demo should show indexing documents, asking one answerable question with a source citation, asking an unanswerable question and receiving a refusal, and saving/recalling a user memory. Do not show the .env file or a Gemini API key in the recording.

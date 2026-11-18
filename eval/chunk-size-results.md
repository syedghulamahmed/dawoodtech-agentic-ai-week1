# Measured Chunk-Size Comparison

**Run date:** 18 November 2026  
**Provider:** Gemini embeddings (gemini-embedding-001)  
**Metric:** Expected-source retrieval hit@5 over the 15 answerable evaluation questions.

| Chunk size (characters) | Overlap (characters) | Chunks | Expected-source hit@5 |
|---:|---:|---:|---:|
| 500 | 62 | 23 | 15/15 (100.0%) |
| 900 | 112 | 15 | 15/15 (100.0%) |
| 1400 | 175 | 9 | 15/15 (100.0%) |

## Interpretation

All three configurations retrieved the expected source within the top five for all 15 answerable questions in this evaluation. The 900-character configuration is a practical middle ground: it used 15 chunks, compared with 23 at 500 characters and 9 at 1400 characters, while matching the measured hit@5 score.

This is a retrieval-coverage result for this small evaluation set. It does not establish that every generated answer is factually complete, nor does it prove that one chunk size is universally better. Re-run the script when the document collection or question set changes.

# 15-question tool-use evaluation

Run uv run python scripts/run_eval.py after configuring a live provider. The script records actual executed tools in generated result files. Expected tools below are test expectations, not actual results.

| # | Test | Expected tools |
|---:|---|---|
| 1 | Current weather in Multan | get_weather |
| 2 | Current weather in Lahore, Fahrenheit | get_weather |
| 3 | Current weather in Islamabad | get_weather |
| 4 | 235 × 17 + 918 | calculate |
| 5 | (144 ÷ 12) + 7² | calculate |
| 6 | 500 ÷ 8 + 12.5 | calculate |
| 7 | Save a CS midterm revision note | save_note |
| 8 | Save a note explaining BFS and DFS | save_note |
| 9 | Save a project meeting note | save_note |
| 10 | Find the BFS/DFS note | search_notes |
| 11 | Search CS midterm notes | search_notes |
| 12 | Retrieve the project meeting note | search_notes |
| 13 | Multan weather and 7 × 8 | get_weather, calculate |
| 14 | Save a follow-up reminder | save_note |
| 15 | Find BFS note and calculate 64 ÷ 8 | search_notes, calculate |

A tool-selection PASS is not a complete correctness guarantee; inspect returned values and errors too.

# Published evaluation records

These files record the October 26, 2026 submission evaluation:

- `answers.json`: the twelve-case text run, actual contexts, answers, model-judged
  scores and reasons, latencies and configuration fingerprints.
- `answers.csv`: the corresponding questions, answers, scores and latencies.
- `retrieval.json`: ten offline development retrieval cases.
- `scenarios.json`: four database, combined-source and conversation checks, with
  observed answers and source-review notes.

See `docs/evaluation_results.md` for analysis, including retrieval misses and
errors in the judge's own explanations. Raw scores are preserved. These are custom
Gemini rubric estimates, not official RAGAS scores. The small benchmark and
scenario checks do not establish general reliability.

Runtime checkpoints and scratch generations stay under ignored
`evaluation/reports/`. Reproductions should write there rather than overwrite
these records.

# Evaluation datasets

`retrieval.json` contains ten development cases with a question, supporting page
and required evidence phrase. `warhammer-rag evaluate-retrieval` reports hit rate
and mean reciprocal rank at five. These cases informed development and are not a
held-out answer benchmark.

`text.json` contains twelve generated, source-reviewed text questions with
reference answers and exact source quotations. Four summary, four single-hop and
four multi-hop cases cover movement, attacks, missions and stratagems. Source and
chunk hashes identify the supplied edition. Review changes are recorded in the
file. `text_draft.json` preserves the unreviewed model output and must not be used
as the evaluation dataset.

Run the frozen benchmark with `warhammer-rag evaluate-answers`. To generate a
separate draft, use `warhammer-rag generate-eval --output PATH`; references must
be reviewed before evaluation. Use the same frozen version for comparisons.

The text benchmark does not measure database analytics or full conversations.
SQL, combined evidence and follow-up handling have offline regression tests;
live scenario checks and their limits are described with the
[results](../../docs/evaluation_results.md).

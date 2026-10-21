# Evaluation datasets

`retrieval.json` contains ten development cases with a question, supporting page
and required evidence phrase. `warhammer-rag evaluate-retrieval` reports hit rate
and mean reciprocal rank at five. These cases test retrieval only and informed
baseline development; they are not a held-out answer benchmark.

The broader evaluation set covering SQL, combined answers, conversation, missing
evidence and source conflicts remains to be built. Each case should include
question/history, reference facts, supporting pages or database IDs and snapshot
identity. System comparisons must use the same dataset version.

`warhammer-rag generate-eval` creates a separate nine-case draft text benchmark
in `text.json`. References require source review before answer evaluation. See
[the evaluation workflow](../../docs/evaluation.md) for generation, checkpointing
and model-judged metric definitions. A live benchmark has not yet been generated.

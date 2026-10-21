# Text evaluation

The text benchmark follows the Lab 3 workflow: generate questions, review their
references, run the application, save the evidence it actually used, and score
answers. SQL unit tests remain separate.

## Commands

```sh
./scripts/uv run warhammer-rag generate-eval
./scripts/uv run warhammer-rag evaluate-answers --limit 3
./scripts/uv run warhammer-rag evaluate-answers
```

These commands call the configured Gemini model. Generation sends selected
rulebook chunks; evaluation sends questions, reference evidence, actual retrieved
contexts and generated answers. They use the existing Google SDK and do not
require RAGAS or additional evaluation dependencies.

Generation creates nine draft cases: three summary, three single-hop and three
multi-hop questions across movement/core concepts, attacks and mission rules.
Every quoted reference must match its source chunk exactly. This check establishes
provenance, not the correctness or completeness of the reference answer. Review
all cases against the cited chunks and source PDF, then set `review_status` to
`reviewed` in `evaluation/datasets/text.json`. A multi-hop case must genuinely
require both sources, not merely cite two chunks. The evaluation refuses pending
benchmarks. No generated benchmark or live scores have yet been published.

Generation checkpoints each validated three-question batch. Re-running resumes
unfinished generation if the model, sources and generator implementation match.
Use `--output` for a different dataset. Reviewed datasets cannot be overwritten.

Evaluation saves each answer before requesting its scores. Re-running the same
command resumes unfinished scoring without repeating completed answers. Use a
new output path when the dataset, model, index, database or implementation changes;
incompatible checkpoints are rejected. Do not run concurrent writers against the
same output file. JSON holds references, actual sources, answer paragraphs,
latency, per-metric explanations and safe failure diagnostics. CSV contains the
completed answers and scores. Full run output stays under ignored
`evaluation/reports/`; reviewed results and conclusions can be published separately.

## Scoring and interpretation

The current scorer uses a structured Gemini rubric, **not official RAGAS metrics**:

- Faithfulness: support for answer claims in the contexts the agent actually saw.
- Factual correctness: agreement with and coverage of the reviewed reference.
- Context precision: relevance of retrieved contexts to the question.
- Context recall: reference facts supported by the retrieved contexts.

Each score is in [0,1] and includes a reason. When the application retrieves no
contexts, context precision and recall are forced to zero. The evaluator never
substitutes reference evidence for the application's contexts. Routing failures
therefore affect the results.

These are model-judged estimates, not exact claim-level measurements. Using the
same model for generation, answering and judging can introduce correlated bias.
Review failures and a sample of high scores manually. A nine-case benchmark is
small, covers only selected topics and cannot establish general reliability.
Freeze a reviewed dataset before comparing changes; keep the ten existing
retrieval development cases separate. No token-use measurements are claimed.

## Request pacing

`GOOGLE_REQUESTS_PER_MINUTE` defaults to 10. Chat, generation, evaluation and the
connection check share a SQLite-backed call scheduler under ignored `data/local/`.
It spaces requests across processes in the same checkout; it does not change
Google's quota or coordinate other applications/checkouts using the account.
Retries also reserve a request slot. Configure the rate to match the project's
actual limits. Authentication and quota errors are not automatically retried.

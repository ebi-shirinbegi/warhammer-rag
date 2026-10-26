# Text evaluation

The text benchmark follows the Lab 3 workflow: generate questions, review their
references, run the application, save the evidence it actually used, and score
answers. SQL unit tests remain separate.

## Commands

```sh
./scripts/uv run --locked warhammer-rag evaluate-answers --limit 3
./scripts/uv run --locked warhammer-rag evaluate-answers
```

These commands use the included reviewed benchmark. To generate a separate draft:

```sh
./scripts/uv run --locked warhammer-rag generate-eval --output evaluation/reports/text-draft.json
```

Review a new draft before setting its `review_status` to `reviewed`, then evaluate
it with `evaluate-answers --dataset PATH --output NEW_RUN_PATH`. Do not overwrite
the published benchmark or mix results from different question sets.

Generation and answer evaluation call the configured Gemini model. Generation sends selected
rulebook chunks; evaluation sends questions, reference evidence, actual retrieved
contexts and generated answers. They use the existing Google SDK and do not
require RAGAS or additional evaluation dependencies.

Generation creates twelve draft cases: four summary, four single-hop and four
multi-hop questions across movement/core concepts, attacks, missions and stratagems.
Whitespace differences from PDF line breaks are restored to the source form.
Every stored reference quote must then match its source chunk exactly. This check establishes
provenance, not the correctness or completeness of the reference answer. Review
all new cases against the cited chunks and source PDF, then set `review_status` to
`reviewed` in the new draft file. A multi-hop case must genuinely
require combining information from distinct rulebook passages, not merely cite
two chunks containing the same rule. The evaluation refuses pending
benchmarks. The reviewed benchmark is versioned in `evaluation/datasets/text.json`.
The original model drafts are preserved separately in `text_draft.json` with an
unreviewed label. Review notes record corrections to questions and references.
Use the reviewed file for evaluation. To generate a different draft without
overwriting it, pass `--output evaluation/reports/new-draft.json`.

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
Review failures and a sample of high scores manually. A twelve-case benchmark is
small, covers only selected topics and cannot establish general reliability.
The dataset was frozen before the first answer run. Keep the ten existing
retrieval development cases separate. No token-use measurements are claimed.

## Request pacing

`GOOGLE_REQUESTS_PER_MINUTE` defaults to 10. Chat, generation, evaluation and the
connection check share a SQLite-backed call scheduler under ignored `data/local/`.
It spaces requests across processes in the same checkout; it does not change
Google's quota or coordinate other applications/checkouts using the account.
Retries also reserve a request slot. Configure the rate to match the project's
actual limits. Authentication and quota errors are not automatically retried.

## Benchmark review

All twelve references were compared with their cited source text before running
answers. PDF review included the attack table and the stratagem and mission pages.
The review corrected two nominal multi-hop questions that originally cited
redundant evidence, restored a discontinuous quotation, clarified movement timing,
and added missing save and objective-control conditions. Exact quotations establish
provenance; the reference review establishes whether they answer the question.

The dataset has four questions of each type. Its topic groups were selected for
coverage of core mechanics and the assignment's examples, not sampled at random.
Twelve cases follow the small-set scope allowed in Session 1; they do not meet the
broader 50-100-row starting recommendation in Session 2. The benchmark is separate
from the ten retrieval cases used during development, but overlaps their topics.

The rubric was chosen to reuse the application's Google SDK, structured responses
and rate scheduler. It saves actual answers and contexts before judging, making
failures inspectable and interrupted runs resumable. This avoids additional model
and embedding adapters, but loses the standard definitions and implementation of
RAGAS metrics. In particular, context precision here measures the estimated share
of relevant contexts; it is not RAGAS's rank-weighted context precision. No claim
is made that these results are equivalent to RAGAS scores.

## Published evidence

The final run and source-based review are recorded in
[results](evaluation_results.md). Full benchmark results are versioned under
`evaluation/results/`; scratch runs under `evaluation/reports/` remain ignored.
Scores are estimates from one configured model, not guarantees or a pass mark.

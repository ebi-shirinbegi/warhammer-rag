# Evaluation results

Run date: October 26, 2026. The live run uses Google AI Studio with the model ID
recorded in the result files. It evaluates the frozen twelve-case text benchmark
through the same `ChatService` used by the browser. The generator, application and
judge use the same model, so their errors can be correlated.

## Reproduction

After setup, API configuration and index creation:

```sh
./scripts/uv run --locked warhammer-rag evaluate-retrieval
./scripts/uv run --locked warhammer-rag evaluate-answers \
  --dataset evaluation/datasets/text.json \
  --output evaluation/reports/reproduction.json
```

Use a new output filename if the model or implementation changes. Matching
checkpoints resume without regenerating completed answers. API calls consume the
configured project's quota. Model responses and judge scores can vary between
runs; the published files preserve the actual observed output.

## Text benchmark

All **12 of 12** cases completed answering and scoring with
`gemini-3.5-flash-lite`. Ten responses returned `answer`; two returned
`insufficient`. The latter remain in the results and are not excluded from averages.

| Model-judged estimate | Mean score (0 to 1) |
|---|---:|
| Faithfulness | 1.000 |
| Factual correctness | 0.942 |
| Context precision | 0.452 |
| Context recall | 0.958 |

Answer latency: mean **39.5 seconds**, median
**31.6 seconds**, range **9.0-104.3 seconds**.

The full run contains dataset, source, model, index and implementation fingerprints:
[JSON records](../evaluation/results/answers.json) and
[CSV answers and scores](../evaluation/results/answers.csv).

| Case | Type | Answer status | Correctness estimate |
|---|---|---|---:|
| text-01 | summary | answer | 1.00 |
| text-02 | single_hop | answer | 1.00 |
| text-03 | multi_hop | insufficient | 0.50 |
| text-04 | summary | answer | 1.00 |
| text-05 | single_hop | answer | 1.00 |
| text-06 | multi_hop | answer | 1.00 |
| text-07 | summary | answer | 1.00 |
| text-08 | single_hop | insufficient | 0.80 |
| text-09 | multi_hop | answer | 1.00 |
| text-10 | summary | answer | 1.00 |
| text-11 | single_hop | answer | 1.00 |
| text-12 | multi_hop | answer | 1.00 |

These are custom Gemini rubric estimates, not official RAGAS metrics. The raw
score explanations are included in the JSON. The mean scores must not be read as
proof that every answer is correct or that retrieval is consistently precise.

## Source-based review

The answer review found useful distinctions that the aggregate scores conceal:

- `text-03`, distance measurement and Engagement Range: retrieval found how to
  measure distance but missed the definition of Engagement Range. The assistant
  disclosed the missing evidence rather than inventing the distance thresholds.
  Correctness and context recall were both scored 0.5.
- `text-04`, saving throws: the answer explained armour, invulnerable saves and
  cover. It said to make one saving throw but did not explicitly discuss selecting
  among multiple invulnerable saves, which is included in the reference.
- `text-07`, objective control: the answer correctly explained the OC total and
  moving over markers, but did not give the reference's 3-inch horizontal and
  5-inch vertical range. The judge nevertheless assigned correctness 1.0.
- `text-08`, Only War marker placement: the answer found the correct 6-inch and
  9-inch restrictions but unnecessarily questioned whether they applied to Only
  War and omitted the inch notation in its prose. PDF page 59 is the Only War
  mission. The retrieved passage carries a local subsection title, so the broader
  mission context is less clear to the generator. The judge's explanation also
  incorrectly described that passage as general rules rather than this mission.

The judge sometimes miscounts relevant contexts. For example, `text-01` names
only one relevant context among eight but assigns precision 0.25; the stated
fraction would be 0.125. `text-06` names two relevant contexts among eight but
assigns 0.5. Raw scores are preserved, not silently corrected. Context-precision
scores should therefore be treated as rough judgments; exact counts would need
per-context relevance labels and deterministic aggregation.

## Database and conversation scenarios

Four additional scenarios use the actual application and are saved in
[`scenarios.json`](../evaluation/results/scenarios.json):

| Scenario | Observed result |
|---|---|
| Exact Intercessor Squad Toughness | Returned 4 from SQLite with a datasheet citation, without model generation |
| Intercessor Squad grenade eligibility | Combined the database keyword with the PDF's CP cost, timing, engagement, shooting and target restrictions |
| Follow-up asking for wounds | Resolved the previous unit and returned Wounds 2 |
| Generic Space Marine Toughness | Asked for a specific unit rather than inventing a universal statistic |

These are small functional checks, not a statistically representative database
or multi-turn benchmark. They do not establish reliability for arbitrary SQL
questions, unsupported units or every source-version conflict.

## Retrieval baseline and setup

The ten development retrieval cases achieved hit rate at 5 of **1.00** and mean
reciprocal rank at 5 of **0.875**. These cases informed development, so their scores
must not be treated as held-out performance. Their complete output is in
[`retrieval.json`](../evaluation/results/retrieval.json).

A fresh source copy passed installation, index creation, all 75 offline tests and
an HTTP check without API credentials. See [verification](verification.md).

## Conclusions and limitations

The application can combine rulebook and datasheet evidence, retain conversation
context and decline unsupported parts of a question. Retrieval still introduces
irrelevant passages and can miss one rule needed for a compound question. Source
citations alone do not guarantee completeness, and the model judge can overlook
omissions or make arithmetic errors.

The measured weaknesses suggest two specific next improvements: preserve parent
section and mission titles in answer context, and retrieve separate evidence for
each part of compound questions. Those changes should be compared on the same
frozen benchmark and a larger independent set. No before/after improvement is
claimed in this submission.

Twelve selected text questions and four conversation scenarios are too small to
establish general reliability. They cover one supplied corpus version, one model
and one live run. Answer latency includes retrieval, local rate-limit waiting and
any retries, but excludes the subsequent judging call. The scenario checks shared
the API scheduler during part of this run. Token use and monetary cost were not
measured, and no production monitoring service is included.

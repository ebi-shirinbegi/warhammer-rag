# Project requirements

## Scope

A multi-turn Warhammer 40,000 chatbot using the supplied Core Rules PDF and SQLite
unit database. Supported questions must include text-only, database-only and
combined-source cases. The LLM backend is Google AI Studio.

Authors: Mohammad Ebrahim SHARIFI and Muhammad Ibrar Ul HASSAN.

## Assignment requirements

Page references use the supplied PDFs' 1-based page numbers.

| Requirement | Source | Acceptance evidence |
|---|---|---|
| Correct parsing of the complex rulebook | Lab 1 p2; Session 1 p40 | Reviewed structured output with source pages |
| Text and SQLite retrievers | Session 1 p40 | Relevant passages and correct structured results |
| Combined-source answers | Session 1 p39 | Questions requiring evidence from both sources |
| Multi-turn conversation | Lab 1 p2 | Follow-up resolution using conversation history |
| Generated evaluation dataset and pipeline | Session 1 p40 | Reviewed, versioned questions and repeatable results |
| Unit tests | Session 1 p41 | Runnable offline test suite |
| Google AI Studio backend | Session 1 p41 | Configurable Google API integration |
| Modular, documented code | Session 1 pp41-42 | Clear package boundaries and setup documentation |
| Runnable chat, tests and evaluation | Session 1 p42 | Documented entry points |
| Parsed rulebook delivered with repository URL | Lab 2 p2 | Versioned parse artifact and accessible repository |
| Credentials excluded from Git | Lab 2 p5 | Local `.env` and tracked configuration template |
| Both students clearly identified in the repository | October 22 announcement | Names in the README and application footer |
| Technical choices and their justifications | October 22 announcement | Architecture decisions, tradeoffs and evaluation method |
| Repository link sent by email | October 22 announcement | Submission by the students |

Source references: Lab 1, Lab 2, Lab 3, Session 1 and the October 22 announcement. Assignment and lecture documents
are local reference material and are not distributed with the repository.

## Submission and assessment

- Deadline stated in Lab 2 p2 and repeated in Lab 3 p2: **November 2nd, 00:00**. Year and timezone are not
  specified. This denotes the start of November 2.
- Submission: email the repository URL to the instructor, as specified on October 22.
  Include the parsed rulebook in the repository, as allowed by Labs 2 and 3.
  The October 22 announcement does not change the project deadline.
- Team size: two. Project: 8/20 course points. Individual quiz: 12/20.
- Project assessment areas: RAG setup, evaluation and monitoring, advanced RAG,
  interface, and code quality. Subweights are not specified.
- No separate presentation, report format or hosted deployment is specified.

The example questions in Session 1 p42 cover grenades, stratagem use, scoring and
Space Marine toughness. The last requires an explicit unit assumption or entity
clarification: Intercessor and Heavy Intercessor profiles differ.

## Design constraints

The framework and architecture are open choices (Session 1 p41). Lab 2 p3 marks
its folder layout and library examples as suggestions. LangGraph and Textual are examples. Lab 3 p3 also marks its implementation
slides as suggestions; its demonstrated evaluator uses RAGAS. This project uses
a custom Gemini rubric and documents the difference in `evaluation.md`.

Session 1 p40 permits a small generated evaluation set, with ten questions given
as an example. Session 2 pp35-40 recommends a larger starting set for broader
coverage. Generated reference answers require review; comparisons use a frozen,
versioned dataset. Evaluation separates retrieval quality, grounding, correctness,
latency and resource use.

## Lab 3 clarification (reviewed October 16, 2026)

The supplied `project instructions.pdf` is byte-for-byte identical to Lab 1;
it introduces no changed requirements. Lab 3 repeats the existing deadline and
submission artifacts. Page 3 explicitly labels the implementation examples as
suggestions and focuses this lab on text-based evaluation, excluding T2SQL
testing from that exercise. This does not remove SQLite from the project scope.

The complete `Mini-Project-20261016` package was also checked. Its Lab 2, Lab 3
and project instructions PDFs are byte-for-byte identical to the reviewed copies.
Its `Input data.zip` contains only the Core Rules PDF, `wahadb.sqlite` and the SQL
data dictionary; all three match the existing project files byte-for-byte.
This package introduces no additional instructions or changed input data.

Lab 3 provides the following evaluation workflow:

- Generate and save a dataset containing summary, single-hop and multi-hop
  questions using RAGAS and parsed sections represented as LangChain documents
  (p5).
- Run questions through the application and persist reference answers, generated
  responses and contexts actually used by the agent, with resumable checkpoints
  (pp6-7). Retrieval skipped by the router must count against the evaluation;
  separately retrieved ideal contexts must not replace the agent's contexts.
- Measure faithfulness, factual correctness, context precision with reference
  and context recall; export per-question scores and responses (p7).
- Keep evaluation dependencies in a separate `eval` group; RAGAS and RapidFuzz
  are the example packages (p4). Gemini and embedding adapters are shown on p9.
- Use a shared request-rate limiter for Gemini calls, including evaluation calls
  (p13). Serializing concurrent requests alone does not enforce a per-minute limit.

Makefile commands, SBERT adapters and excluding large raw PDFs/SQLite files are
implementation examples, not new mandatory architecture choices (pp9-11).
API credentials must remain excluded from Git (p11).

Evaluation includes ten development retrieval cases plus commands for generated
text benchmarks, resumable answer runs and structured model-judged scoring. Shared
Gemini request pacing is implemented. The scorer uses an explicit rubric, not
official RAGAS metrics. The generated text benchmark contains twelve reviewed
cases across four topic groups; see `evaluation.md` for the method and recorded
results. Existing SQL unit tests remain part of the offline suite.

## Delivery milestones

| Milestone | Completion criterion |
|---|---|
| Foundation | Reproducible setup, preserved inputs, configuration and offline tests |
| Ingestion | Complete reviewed parse with graphical tables and page provenance |
| Retrieval | Text and SQL channels return correct, traceable evidence |
| Conversation | Source routing, combined answers and follow-ups operate through the interface |
| Evaluation | Frozen cases, baseline metrics and measured improvements |
| Release | Clean-checkout execution of chat, tests and evaluation with supplied parsed artifacts |

The repository is public. The deadline year and timezone are not stated in the
lab slides. Source precedence remains unspecified where the supplied PDF and
database disagree; answers must retain that distinction.

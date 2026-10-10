# Project requirements

## Scope

A multi-turn Warhammer 40,000 chatbot using the supplied Core Rules PDF and SQLite
unit database. Supported questions must include text-only, database-only and
combined-source cases. The LLM backend is Google AI Studio.

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
| Modular, documented code | Session 1 pp41–42 | Clear package boundaries and setup documentation |
| Runnable chat, tests and evaluation | Session 1 p42 | Documented entry points |
| Parsed rulebook delivered with repository URL | Lab 2 p2 | Versioned parse artifact and accessible repository |
| Credentials excluded from Git | Lab 2 p5 | Local `.env` and tracked configuration template |

Source references: Lab 1, Lab 2 and Session 1. Assignment and lecture documents
are local reference material and are not distributed with the repository.

## Submission and assessment

- Deadline stated in Lab 2 p2: **November 2nd, 00:00**. Year and timezone are not
  specified. This denotes the start of November 2.
- Submission: repository URL and parsed rulebook; the latter may be included in
  the repository.
- Team size: two. Project: 8/20 course points. Individual quiz: 12/20.
- Project assessment areas: RAG setup, evaluation and monitoring, advanced RAG,
  interface, and code quality. Subweights are not specified.
- No separate presentation, report format or hosted deployment is specified.

The example questions in Session 1 p42 cover grenades, stratagem use, scoring and
Space Marine toughness. The last requires an explicit unit assumption or entity
clarification: Intercessor and Heavy Intercessor profiles differ.

## Design constraints

The framework and architecture are open choices (Session 1 p41). Lab 2 p3 marks
its folder layout and library examples as suggestions. LangGraph, Textual and
RAGAS are options, not individually mandatory dependencies.

Session 1 p40 permits a small generated evaluation set, with ten questions given
as an example. Session 2 pp35–40 recommends a larger starting set for broader
coverage. Generated reference answers require review; comparisons use a frozen,
versioned dataset. Evaluation separates retrieval quality, grounding, correctness,
latency and resource use.

## Delivery milestones

| Milestone | Completion criterion |
|---|---|
| Foundation | Reproducible setup, preserved inputs, configuration and offline tests |
| Ingestion | Complete reviewed parse with graphical tables and page provenance |
| Retrieval | Text and SQL channels return correct, traceable evidence |
| Conversation | Source routing, combined answers and follow-ups operate through the interface |
| Evaluation | Frozen cases, baseline metrics and measured improvements |
| Release | Clean-checkout execution of chat, tests and evaluation with supplied parsed artifacts |

Open assignment details: deadline year/timezone, submission destination and
repository access requirements. Source precedence remains unresolved where the
supplied PDF and database disagree; answers must retain that distinction.

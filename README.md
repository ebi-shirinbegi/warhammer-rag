# Warhammer RAG

Class project by **Mohammad Ebrahim SHARIFI** and **Muhammad Ibrar Ul HASSAN**.

A conversational retrieval-augmented generation project for Warhammer 40,000,
combining the Core Rules PDF with a SQLite database of unit datasheets.
The application supports rule lookups, structured queries, questions requiring
both sources, and conversational follow-ups through Google AI Studio.

## Status

The application includes a parsed 60-page rulebook, text search, read-only SQLite
unit lookups, and a local browser chat with citations and saved conversations.
Google AI Studio provides planning and answer generation. Exact unit-stat lookups
can run without an API call. Offline tests and separate retrieval and answer
evaluation commands are included. See [evaluation](docs/evaluation.md) for the
benchmark, scoring method and limitations. The published run includes twelve
text questions and four live database/conversation scenarios;
[results and known weaknesses](docs/evaluation_results.md) are included.

## Setup

Requirements: macOS or Linux, Git, Python 3 with `venv`, and internet access for
initial dependency installation. The development interpreter is Python 3.12;
application and development dependencies are locked in `uv.lock`.

```sh
./scripts/setup.sh
./scripts/uv run --locked warhammer-rag doctor
./scripts/uv run --locked warhammer-rag index
```

The setup script installs project-local uv and Python, creates `.venv`, synchronizes
locked dependencies and installs the pre-commit hook. Tooling and caches remain
inside the checkout; system Python and shell profiles are unchanged.

## Configuration

Create `.env` from `.env.example` if no local configuration exists:

```sh
cp -n .env.example .env
```

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Google AI Studio API key |
| `GOOGLE_MODEL` | Model identifier available to the configured account |
| `GOOGLE_REQUESTS_PER_MINUTE` | Shared request pacing, default 10; set to your project limit |
| `RAG_PROJECT_ROOT` | Optional checkout path override |
| `RAG_RAW_DIR` | Source directory; defaults to `data/raw` |
| `RAG_PROCESSED_DIR` | Parsed output; defaults to `data/processed` |
| `RAG_INDEX_DIR` | Retrieval indexes; defaults to `data/indexes` |
| `RAG_EVAL_DIR` | Evaluation fixtures; defaults to `evaluation/datasets` |
| `RAG_REPORT_DIR` | Run reports; defaults to `evaluation/reports` |

Edit the local `.env` file and fill in both fields:

```dotenv
GOOGLE_API_KEY=your_google_ai_studio_api_key
GOOGLE_MODEL=your_available_model_id
```

Use the model's API identifier from your own Google AI Studio project. Both values
are placeholders above. The application uses your project's API access and limits;
a Gemini app subscription is not required by the code. No key is included in this
repository. Keep `.env` local; do not put credentials in `.env.example`.

Then start the browser interface:

```sh
./scripts/uv run --locked warhammer-rag check-api
./scripts/uv run --locked warhammer-rag chat
```

The parsed rulebook and source database are included, so parsing is not required
to try the application. Building the index once is required. For a first question,
try "How does scoring work in the Only War mission?". A question such as
"Can an Intercessor Squad use grenades?" exercises both source channels.

Commands run from the repository root. Settings load `.env` from the current
working directory; environment variables take precedence. Relative data paths
resolve against the project root. Credentials are excluded from Git and masked
in configuration representations.

`doctor` checks local files and database connectivity without calling an API.
`doctor --require-api-key` additionally requires a nonempty key; it does not
validate credentials remotely. Offline development does not require a key.

To validate the configured model with one small API request:

```sh
./scripts/uv run --locked warhammer-rag check-api
```

This command uses the API quota of the Google AI Studio project associated with
the key. It does not change billing settings.

## Rulebook parsing

```sh
./scripts/uv run --locked warhammer-rag parse
```

The parser writes [readable Markdown](data/processed/core_rules.md),
[structured records](data/processed/core_rules.json) and a
[coverage report](data/processed/parse_report.json). It runs locally without an API
key and checks the source hash before applying the supplied edition's layout profile.
`--output-dir PATH` overrides the destination.

All 60 pages are accounted for, including three decorative pages. All 11 stratagems
retain their costs and conditions. Graphical dice values use reviewed transcriptions;
spatial illustrations remain linked to the PDF rather than fully encoded as text.
See [ingestion details](docs/ingestion.md) for verification and limitations.

## Chat

```sh
./scripts/uv run --locked warhammer-rag chat
```

The command opens **http://127.0.0.1:8000** in your default browser and reuses
an already-running instance from this checkout. Use `--no-browser` to suppress
automatic opening. Configure `.env` and run `warhammer-rag index`
first. Imperial Archive includes source citations, unit clarification, follow-ups and a
History panel. Conversations save locally across refreshes and restarts; saved
records and drafts are excluded from Git. `--port 8001` changes the port. Exact unit-stat questions use SQLite directly. Explicit first-turn lookups use one Gemini answer stage; ambiguous queries and
follow-ups may also need a planning stage, with bounded retries for temporary service errors; the API key stays on the Python server.
See [chat design and limitations](docs/chat.md).

## Evidence retrieval

```sh
./scripts/uv run --locked warhammer-rag index
./scripts/uv run --locked warhammer-rag search "How do I use grenades?"
./scripts/uv run --locked warhammer-rag units "Intercessor"
./scripts/uv run --locked warhammer-rag unit 000001157
./scripts/uv run --locked warhammer-rag search "grenades" --unit "Intercessor Squad"
./scripts/uv run --locked warhammer-rag evaluate-retrieval
```

The index command produces versioned `data/processed/chunks.json` and a rebuildable
SQLite FTS5 index under `data/indexes/`. Search returns JSON evidence with source
identities, pages and ranking scores. These commands run offline without API usage.
An exact, unique unit name resolves to its datasheet; partial or ambiguous names
return candidates. Models, abilities, keywords and cost configurations retain
their stored values and provenance.

These commands return raw evidence. Use `chat` for conversational answers.
Arbitrary question-to-SQL generation is not implemented. See
[retrieval design and baseline results](docs/retrieval.md).

## Development

```sh
./scripts/uv run --locked pytest
./scripts/uv run --locked ruff check .
./scripts/uv run --locked ruff format .
./scripts/uv run --locked pre-commit run --all-files
```

`scripts/check.sh` runs linting, formatting checks, tests and diagnostics.
Pre-commit checks Python files without rewriting them. Dependency changes use
`./scripts/uv add PACKAGE` or `./scripts/uv add --dev PACKAGE`; both
`pyproject.toml` and `uv.lock` belong in the same commit.

## Layout

```text
data/raw/                    Immutable PDF and SQLite corpus
data/processed/              Versioned parsed rulebook and chunks
data/indexes/                Rebuildable indexes, excluded from Git
docs/                        Requirements, architecture and data documentation
evaluation/datasets/         Versioned evaluation fixtures
evaluation/reports/          Local evaluation output, excluded from Git
experiments/docling/          Experimental PDF parser baseline
src/warhammer_rag/            Application package
tests/                       Offline unit tests
scripts/                     Setup and development commands
```

The source corpus is unchanged; hashes and original filenames are recorded in
[the source manifest](docs/source_manifest.json). Course materials remain local and are excluded from Git. Parsed rulebook artifacts belong in version control;
the current Markdown and JSON artifacts are included under `data/processed/`.

## Documentation

- [Requirements](docs/project_brief.md)
- [Architecture and technical choices](docs/architecture.md)
- [Evaluation method](docs/evaluation.md)
- [Evaluation results](docs/evaluation_results.md)
- [Setup verification](docs/verification.md)
- [Ingestion quality criteria](docs/ingestion.md)
- [Database audit](docs/data_audit.md)
- [Source data dictionary](docs/data_dictionary.md)
- [Docling baseline](experiments/docling/README.md)

Tool references: [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Google Gen AI SDK](https://googleapis.github.io/python-genai/).

## Text benchmark evaluation

See [the evaluation workflow](docs/evaluation.md) for generated benchmark review,
resumable answer scoring and limitations. `make generate-eval` generates draft
questions through Gemini into `evaluation/reports/text-draft.json` without replacing
the published benchmark; `make evaluate` evaluates the included reviewed dataset.
`make evaluate-retrieval` runs the existing offline retrieval checks.
`make chat` starts the interface and `make check` runs the offline checks.

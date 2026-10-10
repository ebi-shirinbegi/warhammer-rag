# Warhammer RAG

A conversational retrieval-augmented generation project for Warhammer 40,000,
combining the Core Rules PDF with a SQLite database of unit datasheets.
The target system supports rule lookups, structured queries, questions requiring
both sources, and conversational follow-ups through Google AI Studio.

## Status

Implemented: typed configuration, offline diagnostics, protected SQLite access,
unit tests and development tooling. The earlier Docling parser is retained as an
experimental baseline. Production parsing, indexing, retrieval, conversation and
end-to-end evaluation remain under development.

## Setup

Requirements: macOS or Linux, Git, Python 3 with `venv`, and internet access for
initial dependency installation. The development interpreter is Python 3.12;
application and development dependencies are locked in `uv.lock`.

```sh
./scripts/setup.sh
./scripts/uv run --locked warhammer-rag doctor
./scripts/check.sh
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
| `RAG_PROJECT_ROOT` | Optional checkout path override |
| `RAG_RAW_DIR` | Source directory; defaults to `data/raw` |
| `RAG_PROCESSED_DIR` | Parsed output; defaults to `data/processed` |
| `RAG_INDEX_DIR` | Retrieval indexes; defaults to `data/indexes` |
| `RAG_EVAL_DIR` | Evaluation fixtures; defaults to `evaluation/datasets` |
| `RAG_REPORT_DIR` | Run reports; defaults to `evaluation/reports` |

Commands run from the repository root. Settings load `.env` from the current
working directory; environment variables take precedence. Relative data paths
resolve against the project root. Credentials are excluded from Git and masked
in configuration representations.

`doctor` checks local files and database connectivity without calling an API.
`doctor --require-api-key` additionally requires a nonempty key; it does not
validate credentials remotely. Offline development does not require a key.

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
the complete production parse is still pending.

## Documentation

- [Requirements](docs/project_brief.md)
- [Architecture](docs/architecture.md)
- [Ingestion quality criteria](docs/ingestion.md)
- [Database audit](docs/data_audit.md)
- [Source data dictionary](docs/data_dictionary.md)
- [Docling baseline](experiments/docling/README.md)

Tool references: [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Google Gen AI SDK](https://googleapis.github.io/python-genai/).

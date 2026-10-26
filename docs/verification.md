# Submission verification

Verification date: October 26, 2026.

A fresh source copy was created from the repository files and the proposed
changes. It contained no `.env`, virtual environment, search index, API scheduler
or saved conversations from the development checkout. Setup installed the locked
dependencies and Python 3.12.15 in that copy on macOS arm64.

## Completed checks

| Check | Result |
|---|---|
| `./scripts/setup.sh` | Installed tooling and dependencies, installed the hook, and passed offline diagnostics |
| `./scripts/uv run --locked warhammer-rag index` | Built 161 chunks into a local FTS5 index |
| `./scripts/check.sh` | Ruff checks passed; all 75 tests passed; offline diagnostics passed |
| `./scripts/uv run --locked warhammer-rag evaluate-retrieval` | 10 cases, hit rate at 5 of 1.00 and MRR at 5 of 0.875 |
| Loopback HTTP server | HTML, JavaScript, CSS and the source PDF returned HTTP 200 |
| HTTP chat with no API credentials | Exact Intercessor Squad toughness question returned the cited SQLite value 4 |

The checks emitted PyMuPDF/SWIG deprecation warnings but no test failures.
Linux is supported by the setup scripts but was not tested in this verification.
Live answer evaluation uses the separately configured development checkout; its
model and results are recorded in [evaluation results](evaluation_results.md).
The professor supplies their own key and model ID using the README instructions.

These checks verify installation, local execution and deterministic application
behaviour. They do not guarantee API availability, quota or identical model
responses on another account or at a later date.

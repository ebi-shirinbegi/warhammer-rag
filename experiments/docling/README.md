# Docling parsing baseline

This experiment retains the initial Docling conversion wrapper and CLI from the
repository's earlier implementation. It exports document content to Markdown.
It has not been validated against the complete ingestion quality criteria and is
not the production parser.

From the repository root:

```sh
./scripts/uv run --with 'docling>=2.128.0,<3' python experiments/docling/parse.py \
  data/raw/core_rules.pdf --output data/processed/core_rules_docling.md
```

Docling is an experimental dependency, separate from the locked application
environment. The first execution may download model assets. Record the installed
Docling version, configuration and source hash with benchmark results. Raw output
requires visual review, particularly the graphical wound table, before use as a
submission artifact. See `docs/ingestion.md`.

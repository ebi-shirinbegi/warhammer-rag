# Immutable supplied corpus

`core_rules.pdf` and `wahadb.sqlite` are the supplied originals, renamed/moved
without content changes. SHA-256 values are in `docs/source_manifest.json`.

Do not rewrite the PDF or add indexes/cleaned values to the original database.
Write derived outputs under `data/processed/` or `data/indexes/`.
Database access must be read-only. See `docs/data_audit.md` for source conflicts,
query pitfalls and the recorded snapshot metadata.

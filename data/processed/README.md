# Parsed artifacts

Reviewed Markdown and structured page/section records are stored here.
This directory is versioned because the parsed rulebook is a required deliverable.

- `core_rules.md`: readable extraction of all 60 source pages.
- `core_rules.json`: blocks, page and section identities, bounding boxes, source
  links, graphical transcriptions and an exclusion audit.
- `chunks.json`: retrieval chunks with page ranges, block IDs and continuation links.
- `parse_report.json`: coverage counts and visual interpretation limits.

Rebuild with `./scripts/uv run --locked warhammer-rag parse` from the repository
root. The parser accepts the supplied PDF digest only. Run `warhammer-rag index` after parsing to rebuild chunks and the local index. See `docs/ingestion.md` for the extraction method and checks.

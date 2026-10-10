# Ingestion quality criteria

The supplied rulebook has 60 pages containing native text, multiple columns,
sidebars, graphical tables, diagrams and repeated summaries. Plain text extraction
alone loses rule-bearing information.

## Verification cases

| Pages | Risk | Required handling |
|---|---|---|
| 4 | Miniature example pages introduce duplicate text | Separate thumbnails from the contents guide |
| 9 | D3 conversion values appear as dice graphics | Preserve 1–2 → 1, 3–4 → 2, 5–6 → 3 |
| 21 | Wound thresholds appear as dice graphics | Preserve all strength/toughness comparisons and thresholds |
| 21–22, 34–35 | Rules continue across pages | Retain logical sections with page ranges |
| 37 | Rotated illustrative datasheet | Label as an example; avoid treating it as a live unit profile |
| 41–42 | Dense stratagem cards | Keep name, CP, timing, target, effect and restrictions together |
| 49–52 | Spatial information appears in battlefield photographs | Preserve captions and document visual coverage limits |
| 58–60 | Objective/scoring rules, tables and deployment map | Preserve timing, distances, units and mission scope |

The wound table on p21 requires 2+ when Strength is at least twice Toughness,
3+ when greater but less than twice, 4+ when equal, 5+ when below but greater
than half, and 6+ when at most half. Missing graphical values must be resolved
through visual extraction or reviewed corrections with provenance.

## Output contract

Parsed output includes readable Markdown and structured page/section records,
source hashes, stable identifiers and relevant table/figure links. Complete rules
retain exceptions, keyword applicability and temporal conditions. Navigation
markers, decorative art and duplicate summaries must not overwhelm the index.

The source PDF remains unchanged. Reviewed artifacts are stored in
`data/processed/` and included in the submission. Each page is accounted for,
including decorative pages without rules. Production parsing must pass the
verification cases before retrieval evaluation is meaningful.

## Version scope

The supplied PDF and database contain conflicting rules. Parsing preserves source
wording rather than replacing it with outside knowledge. Only War is the mission
specified by this PDF; its scoring is not generalized to other missions.

# Ingestion quality criteria

The supplied rulebook has 60 pages containing native text, multiple columns,
sidebars, graphical tables, diagrams and repeated summaries. Plain text extraction
alone loses rule-bearing information.

## Extraction method

`warhammer-rag parse` uses PyMuPDF native text blocks in PDF content-stream order.
This preserves the source's columns more reliably than a global vertical sort.
The layout profile is restricted to the supplied file's SHA-256 digest; a different
edition fails before any output is written.

Page 4's thumbnail text, margin navigation and running footers are excluded with
their bounding boxes and reasons recorded in JSON. Wrapped bullet continuations
are reconnected. The page 21 title is moved ahead of its attack sequence.
Stratagem regions on pages 41–42 become atomic records containing the name, cost,
category, timing, target, effect and restrictions where present.

Reviewed transcriptions supply the graphical D3 and wound tables on pages 9 and
21, and preserve battlefield-size cell associations on page 59. CP costs and the
page 60 deployment-map note also carry explicit transcription provenance.
These values come from the supplied PDF, including its older 2CP Heroic Intervention.

The JSON contains stable block IDs, section page ranges and page links. Cross-page
rules remain in their shared section; chunking must preserve continuation context.
Page 37 records are marked `example_only`. Captions and source links preserve access
to battlefield photographs and other illustrations, but the parse does not fully
encode their spatial relationships. Summaries are retained alongside full rules.

The initial PyMuPDF4LLM trial omitted rule text with default settings and mixed
stratagem headings with unrelated card text when graphics were ignored. It is not
a runtime dependency. The earlier Docling implementation remains an experimental
baseline rather than the production extraction path.

## Automated checks

Offline tests verify all 60 page records, unique block identifiers, preservation
of every native-text word unless explicitly excluded, all 11 stratagems and key
restrictions, graphical table values, Only War scoring and step order, example
datasheet labels, source-digest rejection and reproducible output. These checks
complement visual review of the difficult pages; word retention alone does not
prove correct reading order or graphical interpretation.

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

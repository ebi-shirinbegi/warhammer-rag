# Evidence retrieval

## Rulebook index

`warhammer-rag index` builds chunks from the structured parse and a SQLite FTS5
index with the Porter tokenizer and BM25 ranking. This is a reproducible lexical
baseline without embeddings, API calls or a separate database service.

Chunks follow section and heading boundaries. Paragraphs are packed toward a
1,800-character target; individual paragraphs and stratagems are never split to
meet that target. Stratagems remain atomic, including their restrictions. A chunk
can span consecutive pages in the same section. Adjacent chunks with the same
heading carry continuation IDs for later context expansion. The current search
command returns matching chunks without automatically expanding these links.

Cover/introduction pages 1-4, the illustrative datasheet on page 37 and fragments
containing only numbers are excluded from retrieval. They remain in the parsed
artifact. Heading text is indexed separately with increased weight. Chunk IDs,
source digest, pages and original block IDs are retained in results.

Queries become bounded, quoted lexical terms joined with OR; user input cannot
supply SQL or FTS operators. Common question words are removed. One explicit
alias maps general “scoring” questions to “victory points”, except when the query
mentions hits or wounds. This baseline does not provide semantic understanding
of synonyms, negation or conversational references. Scores are ranking values,
not probabilities. The CLI checks the chunk digest against the index metadata
and requires a rebuild when the chunk file changes.

## SQLite unit retrieval

`units NAME` searches literal name substrings and returns at most ten candidates.
`unit ID` retrieves an exact datasheet with models, abilities, distinct keywords,
ordered cost rows, source metadata and snapshot identity. Identifiers remain
strings; stat and cost values are not cast or aggregated. Empty cost rows can be
configuration headings and are preserved.

Inline abilities take precedence over catalog text. Catalog joins use the unit's
faction or a global ability, avoiding the duplicated faction variants identified
in the supplied snapshot. Queries use parameters and a read-only connection.
Detail queries have a SQLite instruction budget; no model-generated SQL is executed.

`search QUERY --unit NAME` returns PDF hits and SQLite evidence in one JSON object.
Only a unique exact unit name is resolved automatically. Ambiguous and partial
names return candidates; no default Space Marine profile is assumed. The two
sources remain separate, including any conflicting rules. This command exposes evidence for inspection; the chat service uses the same
retrieval functions when composing answers.

## Development evaluation

Ten versioned rulebook queries in `evaluation/datasets/retrieval.json` check the
presence of an expected page and fact in the top five results. Run
`warhammer-rag evaluate-retrieval` to save details under `evaluation/reports/`.
The initial 161-chunk baseline has hit rate@5 **1.00** and mean reciprocal rank@5
**0.875**. Eight cases rank first; the Battle-shock case ranks second and the
charge-after-advancing case fourth.

These cases informed development and are not a held-out benchmark. They do not
measure answer correctness, grounding or multi-turn behavior. Separate database
tests cover Intercessor toughness, the six Hive Tyrant abilities, ambiguity,
missing IDs, literal query handling, source immutability and combined evidence.
Answer-level evaluation uses a separate generated and reviewed text benchmark;
see [evaluation](evaluation.md).

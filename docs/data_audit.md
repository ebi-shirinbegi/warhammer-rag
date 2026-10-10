# Supplied database and dictionary audit

Scope: read all of `docs/data_dictionary.md`; inspect `data/raw/wahadb.sqlite` exclusively through SQLite URI `mode=ro`. No source files or database contents were modified. No external URLs were accessed. The supplied Core Rules PDF page 42 was also visually compared with stored stratagem records, using a rendered page image.

## Identity and integrity

- File size: 9,699,328 bytes (about 9.25 MiB).
- SHA-256: `364f412c3c1802d24ccc97eb74ffac78e6a5894a312b2fde685045945595fbc5`.
- `PRAGMA quick_check`: `ok`.
- 21 tables, 167,026 total rows. The dictionary's 21 row counts and every listed column match the supplied database.
- All declared columns are `TEXT`; all inspected actual cell values are strings. No SQL NULL values were found. Missing values use `''`, plus semantic sentinels such as `-`, `N/A`, edition `0`, and the date `01.01.0001 0:00:00`.
- No declared primary keys, foreign keys, NOT NULL constraints, indexes, views or triggers. IDs are meaningful exact strings, commonly with leading zeros. The database is usable for reading, but its analytical optimization is not established by the dictionary's closing claim.
- SQLite text encoding is UTF-8, `user_version = 0`, `schema_version = 105`. UTF-8 storage does not imply the content has been decoded correctly.

## Dataset version and provenance

`last_update.LastUpdate = '2026-09-01 17:05:19'`; no timezone is provided. This is the dataset's recorded refresh time, not evidence that its rules remain current today.

The source table has stored edition labels `0` (30 sources), `10` (7), and `11` (29). Datasheets join to these as follows:

| Stored edition | Datasheets |
|---|---:|
| 11 | 1,091 |
| 10 | 11 |
| 0 | 576 |
| No source ID | 2 |

All faction links and sampled datasheet links use the `wh40k11ed` URL path. These are facts about the supplied files, not independently verified claims about game publication history. Many edition-0 records have source names containing Warhammer Legends or Forge World; do not silently treat edition 0 as a real published edition or convert it to 10/11. A source name can indicate a different context even when its stored edition matches another source.

31 source errata dates use the year-0001 sentinel. Real non-sentinel dates are in `DD.MM.YYYY H:MM:SS` format; lexical sorting of the original strings does not sort them chronologically. Some date/edition combinations deserve caution (for example, the Blood Angels stored edition is 11 and errata date is 22.06.2025). Preserve metadata instead of assuming it is flawless.

Only datasheets have `sourceId`. There is no direct source/edition field on `stratagems`, `abilities`, `enhancements` or `detachments`; therefore an edition filter joined from `source` cannot generally resolve competing global-rule variants. Names are not version identifiers. Keep table, exact ID, relevant unit/detachment context and snapshot provenance with every result.

## Important dictionary corrections

1. **The sample ability query loses half the rule payloads and duplicates others** (dictionary example 2, around line 470). `datasheets_abilities` is both a relation and an inline-rule table. Of 6,985 rows, 3,504 have an empty `abilityId` and carry their own name/description. Selecting only `abilities.name` / `abilities.description` turns these into NULL outputs. The other 3,481 rows refer to catalog abilities. The query must prefer nonblank inline text, fall back to the catalog, and retain `type`, `parameter`, and display order.
2. **`abilities.Id` is not unique.** There are 91 rows but 71 distinct IDs. Thirteen IDs have multiple faction-specific occurrences (up to six). Their name/legend/description payloads agree within each ID in this snapshot, but a plain ID join multiplies results. `(Id, factionId)` is unique here. Matching the datasheet's faction, or the catalog's blank faction for global abilities, covers all nonblank ability links in this snapshot without multiplication.
3. **`datasheets.role` is blank in all 1,680 rows.** Example 6 is titled “by faction and role” but only filters faction; role filtering would not work with this dataset. Role-like questions can use relevant keywords such as Battleline, Character, Monster, Vehicle, etc., when that is what the user means.
4. **`enhancements.supportLeader` is not a boolean-like flag** (line 209). It has 1,015 empty entries and 13 descriptive entries such as `LEADER: KOMMANDOS` or `SUPPORT: SKORPEKH DESTROYERS, ...`. By contrast, `upgrade`, `virtual`, `isSupport` and `isFactionKeyword` use literal text `true`/`false`.
5. **`datasheets.damagedW` contains wound ranges**, e.g. `1-4`, `1-8`, `1-33`; describing it as “damaged-state weapon information” (line 233) is misleading. Pair it with `damagedDescription`.
6. **Identifier capitalization does not require case-normalizing ID values.** SQLite column identifiers such as `Id` and `id` are case-insensitive. Values remain exact strings. Preserve faction IDs such as `AoI`, `AdM`, `LoV`; do not indiscriminately lowercase keys. Normalization can be useful in human name search, not as an automatic substitute for exact joins.
7. **A relation to a stratagem/enhancement is not proof it can be used in the current game state.** Conditions in the rule text, detachment selection, target keywords, timing, and restrictions still apply. Example 4 also omits detachment context, although a unit can have links from several detachments.
8. **The database contains duplicate rows and orphan references**, despite the mostly correct join map. Prefer `EXISTS` or appropriately scoped distinct results for filtering/counting. Check completeness rather than inventing missing parents.

## Concrete ability example

Hive Tyrant `000000460` has six raw ability rows:

1. Deadly Demise, catalog ID `000008339`, parameter `D3`.
2. Leader, catalog ID `000008346`.
3. Shadow in the Warp, catalog ID `000000707`.
4. Synapse, catalog ID `000000705`.
5. Will of the Hive Mind, inline payload and no ability ID.
6. Onslaught (Aura, Psychic), inline payload and no ability ID.

The dictionary query produces eight rows: it duplicates Synapse and Shadow in the Warp for TYR/GC, and returns null names/text for both inline abilities. The following verified query returns six correctly resolved records, retaining parameters:

```sql
SELECT da.line,
       da.type,
       NULLIF(da.abilityId, '') AS ability_id,
       COALESCE(NULLIF(da.name, ''), a.name) AS ability_name,
       COALESCE(NULLIF(da.description, ''), a.description) AS ability_text,
       da.parameter
FROM datasheets AS d
JOIN datasheets_abilities AS da ON da.DatasheetId = d.Id
LEFT JOIN abilities AS a
  ON a.Id = da.abilityId
 AND (a.factionId = d.factionId OR a.factionId = '')
WHERE d.Id = :datasheet_id
ORDER BY CAST(da.line AS INTEGER);
```

Use `:datasheet_id = '000000460'` for this example. The uniqueness and coverage assumptions should be checked if the dataset changes. A future derived catalog could deduplicate identical ability payloads explicitly while preserving the original table and faction links.

## Numeric and row-semantics pitfalls

- Numeric comparisons and ordering over raw TEXT can be wrong. IDs must never be cast to integers; quantities should only be cast after checking the field's semantics.
- Movement has values such as `8"`, `20+"`, `-`; saves/leadership use `2+`, `7+`; toughness includes `5*`; invulnerable saves include `4*` and `-`. All model wounds are integer-shaped strings, but not all stat fields are.
- Weapon attacks/damage/strength can be expressions such as `D6+1`, `2D3`, `D6+6`, or `-`. Range can be `Melee`, `N/A`, a blank string, or a numeric distance. Ballistic/weapon skill is mostly bare numerals, but also includes `3+`, `-`, `N/A`. Do not cast dice expressions to zero or their leading digit.
- `line` and `lineInWargear` are display-order strings. Use numeric order where valid, while preserving raw row identity. `datasheets_wargear.line` is blank in 2,034 rows and cannot be assumed to be a complete unique key.
- 2,813 of 6,276 model-cost rows have blank costs. These include section headings: `YOUR UNIT COSTS`, `YOUR 1ST UNIT COSTS`, `YOUR 2ND + UNIT COSTS`, `WARGEAR OPTIONS`, and others.
- Costs include model-count options, repeated-unit tiers, detachment conditions, and per-weapon surcharges. Preserve headings and line order. Do not sum alternative configurations or label the minimum of every row as the unit price.
- Concrete failure: even after excluding blank costs, `MIN(CAST(cost AS INTEGER))` for Tyrannofex returns 10, a wargear surcharge, while its table also contains a 180 unit-cost row. Casting blank cost to integer returns 0. Both can give a false “cheapest unit” answer.
- 35 `stratagems` records have blank CP cost and describe abilities/actions, with phases such as `Ability "Move"`. The table is broader than its name suggests. A blank CP cost does not mean zero CP.
- A phase can be `Shooting or Fight phase`, `Movement or Charge phase`, or `Any phase`; equality to `Shooting phase` misses relevant records.
- Core/global abilities and stratagems can have blank faction IDs. A faction-only inner join will drop them.

## Duplication, ambiguous names and missing coverage

Exact duplicate extras beyond distinct full rows:

| Table | Extra exact duplicate rows |
|---|---:|
| datasheets_keywords | 4,186 |
| datasheets_leader | 40 |
| datasheets_wargear | 16 |

Other tables have no exact full-row duplicates in this snapshot. This does not mean every candidate key is unique.

`datasheets.Id` is unique, but its 1,680 rows have only 1,291 distinct names. Many units have faction-specific copies, and ten name/faction pairs themselves occur twice (including Terminator Squad, Gladiator variants and several other Space Marine units). Preserve exact datasheet IDs and source context after name resolution.

There are 25 factions, but only 24 own parent datasheets. Unbound Adversaries (`UA`) has no datasheets. Orphan model rows include Greater Daemon, Lesser Daemons, Abomination and Daemonic Beasts, but they should not be silently presented as complete parent datasheets.

Ability rows reference 1,680 distinct datasheet IDs, one of which is an orphan; the matched-parent coverage is therefore 1,679. The missing ability parent coverage should be inspected explicitly rather than inferred from the near-matching count.

Missing normal child coverage:

- Sir Hekhtur `000002770` has a model row but no model-cost row.
- Example Wargear `000003708` has `virtual='true'`, no model row, no model-cost row, and no source ID.
- Knight Destrier `000004213` also has a blank source ID.
- 315 keyword rows have an empty keyword.
- `datasheets.leaderHead` and `datasheets_abilities.model` are entirely empty, so they cannot resolve richer leader/model contexts.

Nonblank orphan references found by exact anti-joins:

| Child relationship | Orphan rows | Distinct missing keys |
|---|---:|---:|
| datasheets_abilities.DatasheetId -> datasheets.Id | 1 | 1 |
| datasheets_keywords.DatasheetId -> datasheets.Id | 24 | 4 |
| datasheets_models.DatasheetId -> datasheets.Id | 4 | 4 |
| datasheets_stratagems.DatasheetId -> datasheets.Id | 13 | 2 |
| datasheets_unit_composition.DatasheetId -> datasheets.Id | 4 | 4 |
| datasheets_wargear.DatasheetId -> datasheets.Id | 24 | 18 |
| datasheets_leader.attachedId -> datasheets.Id | 1 | 1 |
| datasheets_stratagems.stratagemId -> stratagems.id | 9 | 1 |
| stratagems.detachmentId -> detachments.Id | 6 | 1 |

All other documented relations have zero missing nonblank reference values. Blank references are separately meaningful; for example, 67 global stratagems have blank faction and detachment fields, and 3,504 ability-link blanks carry inline rules.

Missing stratagem ID: `000010677006`; missing detachment ID: `000000783`. Missing datasheet IDs include `000004101` and `000004150`–`000004153`, plus 14 older IDs referenced only by wargear in this audit. The detailed key list is saved in `relation_audit.json` in docs/audit.

There are four enhancement links whose parent unit faction differs from the enhancement faction. Do not automatically erase these as errors: relationship context can allow cross-faction application. The corresponding stratagem and detachment-ability links have no nonblank faction mismatches.

Avoid joining every child table into a single wide query: independent one-to-many relationships multiply rows (weapons × costs × keywords × abilities). Fetch coherent evidence groups separately or aggregate each child before joining.

## Text cleaning needs

A scan of every cell found no HTML tags matching an ordinary opening/closing-tag pattern. The supplied SQL content is already mostly flattened plain text; adding a generic HTML scraper is not the main task. HTML entities remain in a few places, e.g. `per T&#x27;au flamer`.

There is substantial encoding corruption (mojibake), including curly apostrophes rendered as `\u00e2\u0080\u0099`, dashes, and some Russian type labels. For instance, the faction names T’au Empire and Emperor’s Children contain these broken apostrophes in the actual DB. ASCII smart-quote substitutions alone will not recover all affected text.

A conservative heuristic (C1 control characters or common Latin-1 UTF-8 misdecode patterns) flags rows in these tables:

| Table | Rows with likely mojibake |
|---|---:|
| abilities | 56 |
| datasheets | 674 |
| datasheets_abilities | 1,089 |
| datasheets_keywords | 117 |
| datasheets_models | 29 |
| datasheets_options | 2,735 |
| datasheets_unit_composition | 258 |
| datasheets_wargear | 1,538 |
| detachment_abilities | 186 |
| detachments | 136 |
| enhancements | 698 |
| factions | 2 |
| source | 4 |
| stratagems | 1,591 |

Counts are heuristic flags, not proof that every flagged character is erroneous. Preserve raw content and apply any validated repair only to derived display/search/embedding text, retaining raw IDs and provenance. Test the repair on apostrophes, em/en dashes, nonbreaking hyphens, and Cyrillic text before generalizing it. Entity unescaping is a separate operation.

Some rules are concatenated with no separators (`WHEN: ...phase.TARGET: ...EFFECT:`). Ability descriptions can contain extracted heading/reference fragments such as `DEADLY DEMISE24.08From...`. Better segmenting these for retrieval should retain the wording and limitations rather than rewrite rules from memory.

## Required-question ambiguity: “What is the toughness of a space marine?”

The supplied DB can answer a named-model statistic, but does not define a single universal toughness for every Space Marine unit.

| Datasheet | ID | Source name | Stored edition | Toughness |
|---|---|---|---|---:|
| Intercessor Squad | 000001157 | Space Marines | 11 | 4 |
| Assault Intercessor Squad | 000001606 | Space Marines | 11 | 4 |
| Heavy Intercessor Squad | 000001177 | Space Marines | 11 | 6 |
| Terminator Squad | 000001183 | Space Marines | 11 | 5 |
| Terminator Squad | 000004138 | Black Templars | 11 | 5 |

Intercessor Squad itself is unique here; do not claim multiple Intercessor IDs. A useful answer should explicitly say it is using the Intercessor Squad as the ordinary example (T4), or ask which unit the user means when the choice matters, and cite the exact model/datasheet used. Name search for `intercessor` must not collapse the Heavy Intercessor profile into the ordinary one.

Verified lookup pattern:

```sql
SELECT d.Id, d.name AS datasheet_name,
       m.name AS model_name, m.t AS toughness,
       s.name AS source_name, s.edition, d.link
FROM datasheets AS d
JOIN datasheets_models AS m ON m.DatasheetId = d.Id
LEFT JOIN source AS s ON s.Id = d.sourceId
WHERE d.Id = :datasheet_id
ORDER BY CAST(m.line AS INTEGER);
```

## Verified conflict between the supplied PDF and SQLite

The comparison below concerns supplied artifacts only. It does not establish the intended source precedence.

Core Rules PDF printed page 42 has GRENADE at 1 CP. Its target is a Grenades unit not in Engagement Range and not selected to shoot in that phase; the effect measures 8-inch range and visibility from the Grenades unit.

Stored stratagem `000008335006` (GRENADE) is also 1 CP, but its target text explicitly excludes a unit that Advanced, Fell Back, or has shot that turn. Its effect selects one Grenades model and measures visibility/range from that model. These are materially different eligibility/measurement instructions, not just stylistic changes.

An even simpler conflict on the same supplied page: PDF HEROIC INTERVENTION costs **2 CP**; both core same-name SQLite records (`000008335012`, `000010810011`) say **1 CP**. The PDF also has TANK SHOCK based on a melee weapon's Strength; do not assume an identically named current-looking database record is the same version.

The database contains several name-colliding global/core sets: COMMAND RE-ROLL, INSANE BRAVERY, FIRE OVERWATCH, HEROIC INTERVENTION, and others. Some phases differ between same-name variants. Neither `FactionId=''` nor `detachmentId=''` uniquely selects a rule version.

The RAG/SQL system should disclose a conflict when both sources are relevant, cite each independently, and keep a documented scope/precedence choice. It should never silently blend their eligibility conditions, CP cost, or damage formula into a synthetic answer.

## Suggested evaluation cases grounded in this snapshot

These are useful data-layer cases for the later implementation, subject to the evaluation protocol:

1. Exact statistic: Intercessor Squad `000001157` has toughness 4; Heavy Intercessor Squad `000001177` has toughness 6. Check entity disambiguation.
2. Inline + catalog ability retrieval: Hive Tyrant must yield six abilities, preserve Deadly Demise's D3 parameter, avoid TYR/GC duplicates, and retain Will of the Hive Mind and Onslaught.
3. Keyword filter with no duplicate units: the TYR Battleline query returns Gargoyles `000000484`, Hormagaunts `000000469`, and Termagants `000000468`.
4. Leader relationship: Hive Tyrant `000000460` can be linked to Tyrant Guard `000000471`; do not infer that every Leader keyword unit leads every infantry unit.
5. Weapon expression: Hive Tyrant's heavy venom cannon has attacks D3, range 36, strength 9, AP -2 and damage 3. Its stranglethorn cannon has D6+1 attacks; keep the expression intact.
6. Conditional costs: Hive Tyrant has a `YOUR UNIT COSTS` heading and `1 model` cost 195. Tyrannofex should expose cost context rather than claim its 10-point weapon option is the unit price.
7. Detachment context: Hive Tyrant has 38 stratagem links spanning global entries plus six named detachments; do not claim all 38 can be used under one chosen detachment without restrictions.
8. Missing data: Sir Hekhtur has no cost record; empty results are not proof of cost zero. Unbound Adversaries has no parent datasheets.
9. Mixed evidence: ask about Heroic Intervention cost or Grenade eligibility and check that PDF/DB disagreement is surfaced.
10. Read-only enforcement: mutation/ATTACH/DDL requests must fail at the tool boundary; answerable selects must remain available.

Keyword-filter pattern that avoids duplicate inflation:

```sql
SELECT d.Id, d.name
FROM datasheets AS d
WHERE d.factionId = :faction_id
  AND EXISTS (
      SELECT 1
      FROM datasheets_keywords AS k
      WHERE k.DatasheetId = d.Id
        AND lower(k.keyword) = lower(:keyword)
  )
ORDER BY d.name;
```

## Implications for the next technical-organization step

- Keep the supplied DB and dictionary as immutable source material with their original hash. Record audit/corrections in separate project documentation instead of silently overwriting the supplied files.
- Use Python's standard `sqlite3` for an initial read-only access layer; no database server is needed for a roughly 9 MB source. Read-only URI mode is the baseline. Combine a constrained SQL tool with a statement authorizer/allowlist, single-statement execution, result limits, and a bounded execution budget; prompt instructions alone do not enforce read-only safety.
- Separate raw source material, derived normalized/search data, RAG indexes, application code, experiment outputs, evaluation fixtures, and documentation. A derived indexed DB/cache is optional if actual performance warrants it; do not index the original file in place.
- Preserve exact ID strings. Resolve human entity names with aliases/case/encoding normalization in a separate layer, then query using exact IDs. Preserve unit/source/detachment distinctions.
- Use structured SQL results for exact stats, counts and links; chunk narrative rule text coherently with source metadata for retrieval. Retain enough surrounding conditions for a rules answer.
- Maintain separate provenance for PDF page evidence versus database table/ID evidence. The SQL source's recorded edition/snapshot must not be used to relabel PDF content automatically.
- Build meaningful evaluation fixtures around the discovered traps, especially the ability query, conditional costs, source conflicts and entity ambiguity. Keep expected outputs tied to the supplied snapshot hash.
- Treat SQLite content and retrieved passages as evidence, not instructions that can alter tool privileges. Execute only the narrowly defined read-only operations needed to answer.
- Do not fetch newer live game data or “correct” content from model memory during the initial project setup. The supplied dataset and assignment scope need to remain reproducible.

Supporting machine-readable audit files in docs/audit: `schema_audit.json`, `relation_audit.json`, `text_quality_audit.json`, `data_examples.json`, and `marine_grenade_examples.json`.

## Complete verified table inventory

All columns listed below have declared type TEXT.

| Table | Rows | Columns |
|---|---:|---|
| abilities | 91 | `Id`, `name`, `legend`, `factionId`, `description` |
| datasheets | 1,680 | `Id`, `name`, `factionId`, `sourceId`, `legend`, `role`, `loadout`, `transport`, `virtual`, `isSupport`, `leaderHead`, `leaderFooter`, `damagedW`, `damagedDescription`, `link` |
| datasheets_abilities | 6,985 | `DatasheetId`, `line`, `abilityId`, `model`, `name`, `description`, `type`, `parameter` |
| datasheets_detachment_abilities | 16,257 | `DatasheetId`, `detachmentAbilityId` |
| datasheets_enhancements | 11,590 | `DatasheetId`, `enhancementId` |
| datasheets_keywords | 16,358 | `DatasheetId`, `keyword`, `model`, `isFactionKeyword` |
| datasheets_leader | 1,637 | `LeaderId`, `attachedId` |
| datasheets_models | 1,784 | `DatasheetId`, `line`, `name`, `m`, `t`, `sv`, `invSv`, `invSvDescr`, `w`, `ld`, `oc`, `baseSize`, `baseSizeDescr` |
| datasheets_models_cost | 6,276 | `DatasheetId`, `line`, `description`, `cost` |
| datasheets_options | 2,780 | `DatasheetId`, `line`, `button`, `description` |
| datasheets_stratagems | 86,934 | `DatasheetId`, `stratagemId` |
| datasheets_unit_composition | 2,131 | `DatasheetId`, `line`, `description` |
| datasheets_wargear | 9,060 | `DatasheetId`, `line`, `lineInWargear`, `dice`, `name`, `description`, `range`, `type`, `a`, `bsWs`, `s`, `ap`, `d` |
| detachment_abilities | 349 | `Id`, `factionId`, `name`, `legend`, `description`, `detachment`, `detachmentId` |
| detachments | 327 | `Id`, `factionId`, `name`, `legend`, `type`, `dp`, `forceDisposition` |
| detachments_chapter_dp | 4 | `DetachmentId`, `keyword`, `dp` |
| enhancements | 1,028 | `FactionId`, `name`, `id`, `cost`, `detachment`, `detachmentId`, `upgrade`, `legend`, `description`, `supportLeader` |
| factions | 25 | `Id`, `name`, `link` |
| last_update | 1 | `LastUpdate` |
| source | 66 | `Id`, `name`, `type`, `edition`, `version`, `errataDate`, `errataLink` |
| stratagems | 1,663 | `FactionId`, `name`, `id`, `type`, `cpCost`, `legend`, `turn`, `phase`, `detachment`, `detachmentId`, `description` |

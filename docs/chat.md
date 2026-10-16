# Imperial Archive chat interface

Run `./scripts/uv run --locked warhammer-rag chat`; it opens
`http://127.0.0.1:8000` in the default browser. Running the command again opens
the existing instance from the same checkout. Use `--no-browser` to suppress
automatic opening. Other services on the port are not reused or stopped. Use `--port 8001` to choose another port. The server
binds only to the local computer and is not a public deployment server.

The server reloads `GOOGLE_API_KEY` and `GOOGLE_MODEL` from the project `.env`
before each question. Exported environment variables take precedence over that
file. Data paths remain fixed for the lifetime of the server.

The browser interface uses an original gothic archive design: brass insignia,
dark green panels, parchment text, responsive chat and an evidence sidebar.
A collapsible desktop sidebar lists saved conversations and highlights the active
chat. On narrow screens it becomes a drawer that closes on selection, outside
click or Escape. The crest and header title return to the welcome screen while
preserving saved conversations.
Suggested questions, keyboard submission, new consultations, loading states and
recoverable error messages are included. Each citation opens the corresponding
record; PDF references also link to the source page.

## Request flow

Simple exact-name questions about Toughness, Movement, Wounds, Leadership and
Objective Control are answered directly from SQLite, with a datasheet citation
and a Verified Datasheet label. This path does not depend on Gemini availability.
First-turn questions with explicit database unit names or recognized rule topics
use local retrieval planning and one Gemini answer stage. Ambiguous questions and
follow-ups use a model planning stage as well. No cross-user answer cache or model
switching is used to bypass API limits. Each stage makes at most three attempts for HTTP 408, 500, 502, 503 or 504,
with exponential backoff and jitter. SDK retries are disabled to avoid multiplying
attempts. Each attempt has a 30-second timeout; authentication and quota errors
are not automatically retried. Persistent outages still produce an error while
retaining the question for resubmission.
A schema-constrained planning request rewrites follow-ups into a standalone query
and selects rulebook retrieval, unit lookup or both. SQLite execution uses fixed,
parameterized queries; the model cannot execute arbitrary SQL. Ambiguous units
return candidate names and IDs for clarification. The browser sends up to twelve
recent messages as model context, while the full conversation is retained locally.
Conversations, citations, source excerpts, drafts and errors are stored in
`data/local/conversations.sqlite`, excluded from Git. Questions are saved before
API calls. Refreshing restores the most recently updated conversation; the History
panel supports reopening, renaming and deleting records. New consultation starts
a separate record without deleting existing ones. A pending question survives a
refresh, but an in-flight answer is not resumed automatically. Saved conversations
are local to this project checkout, not synchronized to other computers.
Previously unsaved conversations cannot be recovered after their browser page closes.

Retrieved rulebook chunks include adjacent same-heading continuations. The answer
request receives source records with local citation IDs and instructions to use
only that evidence. Every factual paragraph in an answer must have a known source
ID. Validation rejects missing and invented IDs. This verifies citation identity,
not semantic entailment; answer-level evaluation is still required. Source-version
conflicts and missing evidence must be stated rather than reconciled by guessing.

Queries, recent history and retrieved passages are sent to Google's API. The API
key remains in the Python process. Browser assets contain no credentials, third-
party scripts or remote fonts. The server serves only fixed assets and the source
PDF, validates Host headers and requires an in-memory request token for chat.
Exceptions are converted to safe messages instead of exposing SDK request details.
One chat request is processed at a time to bound accidental concurrent API usage.

## Scope and limitations

The current SQL channel supports named-unit models, costs, keywords and abilities.
It does not support arbitrary database analytics or weapon-table queries. Lexical
rule retrieval can miss synonyms or retrieve partially relevant passages. Model
responses can still be wrong despite valid citations; inspect the evidence when
rules depend on battlefield state or source edition. No paid billing settings are
changed. Google API availability, quota and model latency determine live response
availability; offline tests use deterministic model substitutes.

The interface fills the viewport; only populated conversation and evidence panes
scroll. The welcome layout adapts its spacing and suggestion layout to short
windows. Starting a new consultation resets the conversation scroll position.

Retry reference: [Google Gemini troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting).

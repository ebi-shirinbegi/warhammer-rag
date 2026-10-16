"""Rebuildable SQLite FTS5/BM25 baseline over versioned rulebook chunks."""

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from warhammer_rag.retrieval.sqlite import readonly_connection

STOP_WORDS = set(
    "a an the is are was were do does how what when which can i my we to of in on for "
    "with and or use using need work works after before it you your me please tell about".split()
)


def build_index(chunks_path: Path, index_path: Path) -> int:
    if chunks_path.resolve() == index_path.resolve():
        raise ValueError("Index must not overwrite the chunk artifact")
    content = chunks_path.read_bytes()
    chunks = json.loads(content)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    # One transaction leaves a previous valid index intact if rebuilding fails.
    with closing(sqlite3.connect(index_path)) as connection, connection:
        connection.execute("BEGIN")
        connection.execute("DROP TABLE IF EXISTS rules")
        connection.execute("DROP TABLE IF EXISTS metadata")
        connection.execute("CREATE TABLE metadata (chunks_sha256 TEXT)")
        connection.execute(
            "INSERT INTO metadata VALUES (?)", (hashlib.sha256(content).hexdigest(),)
        )
        connection.execute(
            "CREATE VIRTUAL TABLE rules USING fts5(heading, section, text, "
            "payload UNINDEXED, tokenize='porter unicode61')"
        )
        connection.executemany(
            "INSERT INTO rules VALUES (?, ?, ?, ?)",
            [
                (c["heading"], c["section"], c["text"], json.dumps(c, ensure_ascii=False))
                for c in chunks
            ],
        )
    return len(chunks)


def search_rules(
    index_path: Path, query: str, limit: int = 5, *, chunks_path: Path | None = None
) -> list[dict]:
    if not 1 <= limit <= 20:
        raise ValueError("Result limit must be between 1 and 20")
    # Distinguish mission scoring from scoring hits. This is a lexical baseline,
    # with one explicit domain alias rather than model-based query rewriting.
    normalized = query.lower()
    if "scoring" in normalized and not re.search(r"\b(hit|hits|wound|wounds)\b", normalized):
        normalized = normalized.replace("scoring", "victory points")
    terms = list(dict.fromkeys(t for t in re.findall(r"\w+", normalized) if t not in STOP_WORDS))[
        :32
    ]
    if not terms:
        return []
    expression = " OR ".join('"' + term + '"' for term in terms)
    with readonly_connection(index_path) as connection:
        if chunks_path is not None:
            expected = hashlib.sha256(chunks_path.read_bytes()).hexdigest()
            actual = connection.execute("SELECT chunks_sha256 FROM metadata").fetchone()[0]
            if expected != actual:
                raise ValueError("Search index is stale; run warhammer-rag index again")
        rows = connection.execute(
            "SELECT payload, bm25(rules, 6.0, 1.0, 1.0, 0.0) AS rank "
            "FROM rules WHERE rules MATCH ? ORDER BY rank, rowid LIMIT ?",
            (expression, limit),
        ).fetchall()
    return [{**json.loads(row["payload"]), "score": -row["rank"]} for row in rows]

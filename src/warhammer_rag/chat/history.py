"""Local conversation persistence, separate from the immutable source corpus."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic import BaseModel, Field


class Conversation(BaseModel):
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    title: str = Field(min_length=1, max_length=100)
    messages: list[dict] = Field(default_factory=list, max_length=500)
    draft: str = Field(default="", max_length=2000)
    error: str = Field(default="", max_length=1000)


class ConversationStore:
    def __init__(self, path: Path):
        self.path = path

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS conversations "
            "(id TEXT PRIMARY KEY, title TEXT NOT NULL, payload TEXT NOT NULL, "
            "updated TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
        )
        return connection

    def save(self, conversation: Conversation):
        with closing(self.connect()) as connection, connection:
            connection.execute(
                "INSERT INTO conversations(id,title,payload) VALUES (?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET title=excluded.title,payload=excluded.payload, "
                "updated=strftime('%Y-%m-%dT%H:%M:%fZ','now')",
                (conversation.id, conversation.title, conversation.model_dump_json()),
            )

    def list(self) -> list[dict]:
        with closing(self.connect()) as connection:
            return [
                dict(zip(("id", "title", "updated"), row, strict=True))
                for row in connection.execute(
                    "SELECT id,title,updated FROM conversations ORDER BY updated DESC, id"
                )
            ]

    def get(self, identity: str) -> dict | None:
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT payload FROM conversations WHERE id=?", (identity,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def delete(self, identity: str):
        with closing(self.connect()) as connection, connection:
            connection.execute("DELETE FROM conversations WHERE id=?", (identity,))

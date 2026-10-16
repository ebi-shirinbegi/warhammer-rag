import pytest
from pydantic import ValidationError

from warhammer_rag.chat.history import Conversation, ConversationStore


def test_history_survives_restart_with_sources_and_failed_draft(tmp_path):
    path = tmp_path / "private/conversations.sqlite"
    record = Conversation(
        id="a" * 32,
        title="Grenades",
        messages=[
            {
                "role": "assistant",
                "paragraphs": [{"text": "Rule", "citations": ["S1"]}],
                "sources": [{"id": "S1", "content": "Evidence", "locator": "p.42"}],
            }
        ],
        draft="What about this unit?",
        error="Quota limit",
    )
    ConversationStore(path).save(record)
    reopened = ConversationStore(path)
    assert reopened.get(record.id) == record.model_dump()
    assert reopened.list()[0]["title"] == "Grenades"
    record.title = "Renamed"
    reopened.save(record)
    assert len(reopened.list()) == 1
    assert reopened.list()[0]["title"] == "Renamed"
    reopened.delete(record.id)
    assert reopened.get(record.id) is None
    assert reopened.list() == []


def test_conversation_ids_are_not_paths_or_sql():
    with pytest.raises(ValidationError):
        Conversation(id="../../.env", title="Invalid")

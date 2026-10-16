from pathlib import Path
from unittest.mock import Mock

import pytest

from warhammer_rag.chat.service import Answer, ChatService, Paragraph, Plan, Question, Turn
from warhammer_rag.config import Settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rule_index(tmp_path_factory):
    from warhammer_rag.retrieval.text import build_index

    directory = tmp_path_factory.mktemp("chat-index")
    build_index(ROOT / "data/processed/chunks.json", directory / "rules.sqlite")
    return directory


@pytest.fixture(autouse=True)
def isolated_rule_index(monkeypatch, isolate_settings, rule_index):
    monkeypatch.setenv("RAG_INDEX_DIR", str(rule_index))


def service(*responses):
    backend = ChatService(Settings(_env_file=None, project_root=ROOT))
    backend.generate = Mock(side_effect=responses)
    backend.local_plan = Mock(return_value=None)
    return backend


def test_combined_answer_carries_database_and_pdf_citations():
    backend = service(
        Plan(query="grenades", route="both", units=["Intercessor Squad"]),
        Answer(
            status="answer",
            paragraphs=[Paragraph(text="Check the restrictions.", citations=["S1", "S2"])],
        ),
    )
    result = backend.ask(Question(question="Can my Intercessors use grenades?"))
    assert {s["kind"] for s in result["sources"]} == {"pdf", "sqlite"}
    assert "Roll six D6" in next(s["content"] for s in result["sources"] if s["kind"] == "pdf")
    assert all(s["source_sha256"] for s in result["sources"])


def test_follow_up_context_is_passed_to_planner_and_answerer():
    backend = service(
        Plan(query="toughness", route="units", units=["Intercessor Squad"]),
        Answer(status="answer", paragraphs=[Paragraph(text="Toughness 4.", citations=["S1"])]),
    )
    history = [Turn(role="user", content="Tell me about Intercessor Squad.")]
    backend.ask(Question(question="What is its toughness?", history=history))
    for call in backend.generate.call_args_list:
        assert call.args[1]["history"][0]["content"] == history[0].content


def test_generic_unit_question_requires_clarification():
    backend = service(Plan(query="space marine toughness", route="units", units=[]))
    result = backend.ask(Question(question="What is a Space Marine's toughness?"))
    assert result["status"] == "clarification"
    assert backend.generate.call_count == 1


@pytest.mark.parametrize("citations", [["S99"], []])
def test_invalid_or_missing_citations_are_rejected(citations):
    backend = service(
        Plan(query="grenades", route="rules"),
        Answer(
            status="answer",
            paragraphs=[Paragraph(text="Unsupported assertion", citations=citations)],
        ),
    )
    with pytest.raises(ValueError, match="linked"):
        backend.ask(Question(question="Grenades?"))


def test_missing_evidence_does_not_trigger_answer_generation():
    backend = service(Plan(query="zzznosuchrulezzz", route="rules"))
    result = backend.ask(Question(question="Unknown rule"))
    assert result["status"] == "insufficient"
    assert backend.generate.call_count == 1


def test_user_can_resolve_ambiguity_with_a_datasheet_id():
    backend = service(
        Plan(query="toughness", route="units", units=["000001157"]),
        Answer(status="answer", paragraphs=[Paragraph(text="Toughness 4.", citations=["S1"])]),
    )
    result = backend.ask(Question(question="Use datasheet 000001157. What is its toughness?"))
    assert result["sources"][0]["locator"] == "Datasheet 000001157"


def test_exact_stat_question_works_without_gemini():
    backend = service()
    result = backend.ask(Question(question="What is the Toughness of an Intercessor Squad?"))
    assert result["response_mode"] == "database_lookup"
    assert result["paragraphs"][0]["text"] == "Intercessor Squad: Toughness 4."
    assert result["paragraphs"][0]["citations"] == ["S1"]
    backend.generate.assert_not_called()


@pytest.mark.parametrize("code,failures,expected_calls", [(503, 2, 3), (503, 3, 3), (403, 1, 1)])
def test_generation_retries_transient_errors_with_a_fixed_budget(
    monkeypatch, code, failures, expected_calls
):
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from google.genai.errors import APIError

    client = MagicMock()
    errors = [APIError(code, {"error": {"message": "service error"}}) for _ in range(failures)]
    client.models.generate_content.side_effect = errors + [
        SimpleNamespace(text='{"query":"grenades","route":"rules","units":[]}')
    ]
    factory = MagicMock()
    factory.return_value.__enter__.return_value = client
    monkeypatch.setattr("warhammer_rag.chat.service.genai.Client", factory)
    sleep = Mock()
    monkeypatch.setattr("warhammer_rag.chat.service.time.sleep", sleep)
    backend = ChatService(Settings(_env_file=None, google_api_key="test", google_model="test"))
    if code == 503 and failures == 2:
        assert backend.generate("plan", {}, Plan).query == "grenades"
    else:
        with pytest.raises(APIError):
            backend.generate("plan", {}, Plan)
    assert client.models.generate_content.call_count == expected_calls
    assert sleep.call_count == expected_calls - 1
    assert factory.call_args.kwargs["http_options"].retry_options.attempts == 1


def test_explicit_unit_question_needs_only_answer_generation():
    backend = ChatService(Settings(_env_file=None, project_root=ROOT))
    backend.generate = Mock(
        return_value=Answer(
            status="answer",
            paragraphs=[Paragraph(text="Check the grenade restrictions.", citations=["S1", "S2"])],
        )
    )
    result = backend.ask(Question(question="Can an Intercessor Squad use grenades?"))
    assert backend.generate.call_count == 1
    assert {s["kind"] for s in result["sources"]} == {"pdf", "sqlite"}


def test_follow_up_still_uses_contextual_planning():
    backend = ChatService(Settings(_env_file=None, project_root=ROOT))
    assert (
        backend.local_plan(
            Question(
                question="And grenades?",
                history=[Turn(role="user", content="Tell me about Intercessor Squad")],
            )
        )
        is None
    )


def test_local_plan_preserves_explicit_comparison_of_overlapping_names():
    backend = ChatService(Settings(_env_file=None, project_root=ROOT))
    plan = backend.local_plan(
        Question(question="Compare Intercessor Squad and Heavy Intercessor Squad")
    )
    assert set(plan.units) == {"Intercessor Squad", "Heavy Intercessor Squad"}

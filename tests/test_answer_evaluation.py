import json
from unittest.mock import Mock

import pytest

from warhammer_rag.config import Settings
from warhammer_rag.evaluation.answers import Scores, digest, evaluate_answers


def test_source_quote_restores_line_breaks_but_rejects_changed_facts():
    from warhammer_rag.evaluation.answers import source_quote

    source = 'Models must be within 2" horizontally\n\nand 5" vertically.'
    assert source_quote(source, 'within 2" horizontally and 5" vertically.') == (
        'within 2" horizontally\n\nand 5" vertically.'
    )
    with pytest.raises(ValueError, match="quote"):
        source_quote(source, 'within 3" horizontally and 5" vertically.')


@pytest.fixture
def evaluation(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, project_root=tmp_path, google_model="test")
    for directory in (settings.raw_dir, settings.processed_dir, settings.index_dir):
        directory.mkdir(parents=True)
    settings.rulebook_path.write_bytes(b"test-pdf")
    settings.database_path.write_bytes(b"test-database")
    (settings.index_dir / "rules.sqlite").write_bytes(b"test-index")
    chunks = settings.processed_dir / "chunks.json"
    quote = "A unit must remain in coherency."
    chunks.write_text(json.dumps([{"id": "c1", "text": quote}]))
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "review_status": "reviewed",
                "chunks_sha256": digest(chunks),
                "source_sha256": digest(settings.rulebook_path),
                "cases": [
                    {
                        "id": "one",
                        "kind": "single_hop",
                        "question": "What is unit coherency?",
                        "reference": quote,
                        "evidence": [{"chunk_id": "c1", "quote": quote}],
                    }
                ],
            }
        )
    )
    service = Mock()
    service.ask.return_value = {
        "status": "insufficient",
        "paragraphs": [{"text": "No evidence", "citations": []}],
        "sources": [],
    }
    service.generate.return_value = Scores.model_validate(
        {
            name: {"score": 0.8, "reason": "A test assessment reason."}
            for name in Scores.model_fields
        }
    )
    monkeypatch.setattr("warhammer_rag.evaluation.answers.ChatService", lambda _: service)
    return settings, dataset, tmp_path / "results.json", service


def test_scoring_uses_actual_contexts_and_resumes_without_repeating(evaluation):
    settings, dataset, output, service = evaluation
    summary = evaluate_answers(settings, dataset, output)
    assert summary["completed"] == 1
    assert summary["means"]["context_recall"] == 0
    payload = service.generate.call_args.args[1]
    assert payload["agent_contexts"] == []
    assert payload["reference_evidence"][0]["id"] == "c1"
    assert output.with_suffix(".csv").exists()
    evaluate_answers(settings, dataset, output)
    assert service.ask.call_count == service.generate.call_count == 1


def test_failed_judge_keeps_answer_and_hides_secrets(evaluation):
    settings, dataset, output, service = evaluation
    scores = service.generate.return_value
    service.generate.side_effect = RuntimeError("key=private-key")
    with pytest.raises(RuntimeError, match="progress saved"):
        evaluate_answers(settings, dataset, output)
    assert "private-key" not in output.read_text()
    assert "response" in json.loads(output.read_text())["records"]["one"]
    service.generate.side_effect = None
    service.generate.return_value = scores
    evaluate_answers(settings, dataset, output)
    assert service.ask.call_count == 1
    assert "error" not in json.loads(output.read_text())["records"]["one"]


def test_changed_model_cannot_mix_with_checkpoint(evaluation):
    settings, dataset, output, _ = evaluation
    evaluate_answers(settings, dataset, output)
    settings.google_model = "different"
    with pytest.raises(ValueError, match="configuration changed"):
        evaluate_answers(settings, dataset, output)


def test_unreviewed_dataset_and_overwrite_are_rejected(evaluation):
    settings, dataset, output, service = evaluation
    with pytest.raises(ValueError, match="overwrite"):
        evaluate_answers(settings, dataset, dataset)
    data = json.loads(dataset.read_text())
    data["review_status"] = "pending"
    dataset.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Review references"):
        evaluate_answers(settings, dataset, output)
    service.ask.assert_not_called()


def test_rate_limiter_coordinates_independent_calls(tmp_path, monkeypatch):
    from warhammer_rag.chat.throttle import wait_for_slot

    monkeypatch.setattr("warhammer_rag.chat.throttle.time.time", lambda: 100.0)
    sleep = Mock()
    monkeypatch.setattr("warhammer_rag.chat.throttle.time.sleep", sleep)
    path = tmp_path / "throttle.sqlite"
    wait_for_slot(path, 10)
    sleep.assert_not_called()
    wait_for_slot(path, 10)
    wait_for_slot(path, 10)
    assert [c.args[0] for c in sleep.call_args_list] == [6.0, 12.0]


def test_dataset_generation_checkpoints_batches_and_rejects_invented_quotes(tmp_path, monkeypatch):
    from warhammer_rag.evaluation.answers import Cases, generate_dataset

    settings = Settings(_env_file=None, project_root=tmp_path, google_model="test")
    settings.processed_dir.mkdir(parents=True)
    settings.raw_dir.mkdir(parents=True)
    settings.rulebook_path.write_bytes(b"pdf")
    quote = "Each model must follow this example rule."
    chunks = [
        {"id": f"c{i}", "text": quote, "pages": [page]}
        for i, page in enumerate([6, 7, 20, 21, 58, 59, 41, 42])
    ]
    (settings.processed_dir / "chunks.json").write_text(json.dumps(chunks))

    def batch(ids):
        return Cases.model_validate(
            {
                "cases": [
                    {
                        "id": kind,
                        "kind": kind,
                        "question": "What does this rule require?",
                        "reference": quote,
                        "evidence": [{"chunk_id": i, "quote": quote} for i in ids],
                    }
                    for kind in ("summary", "single_hop", "multi_hop")
                ]
            }
        )

    service = Mock()
    service.generate.side_effect = [batch(["c0", "c1"]), RuntimeError("network failure")]
    monkeypatch.setattr("warhammer_rag.evaluation.answers.ChatService", lambda _: service)
    output = tmp_path / "benchmark.json"
    with pytest.raises(RuntimeError):
        generate_dataset(settings, output)
    assert json.loads(output.read_text())["batches_completed"] == 1
    service.generate.side_effect = [batch(["c2", "c3"]), batch(["c4", "c5"]), batch(["c6", "c7"])]
    dataset = generate_dataset(settings, output)
    assert len(dataset["cases"]) == 12
    assert dataset["review_status"] == "pending"
    assert service.generate.call_count == 5
    invalid = batch(["invented", "c1"])
    service.generate.side_effect = [invalid]
    with pytest.raises(ValueError, match="quote"):
        generate_dataset(settings, tmp_path / "invalid.json")

import hashlib
import json
from pathlib import Path

import pytest

from warhammer_rag.cli import main
from warhammer_rag.ingestion.chunks import build_chunks
from warhammer_rag.retrieval.datasheets import find_units, retrieve_unit, unit_details
from warhammer_rag.retrieval.text import build_index, search_rules

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/raw/wahadb.sqlite"
CASES = json.loads((ROOT / "evaluation/datasets/retrieval.json").read_text())


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    directory = tmp_path_factory.mktemp("search")
    chunks_path = directory / "chunks.json"
    chunks = build_chunks(ROOT / "data/processed/core_rules.json", chunks_path)
    index_path = directory / "index.sqlite"
    assert build_index(chunks_path, index_path) == len(chunks)
    return index_path, chunks_path, chunks


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_reference_evidence_is_in_top_five(index, case):
    results = search_rules(index[0], case["query"])
    assert any(case["page"] in hit["pages"] and case["contains"] in hit["text"] for hit in results)


def test_stratagems_are_atomic_and_example_profiles_are_excluded(index):
    chunks = index[2]
    grenade = [c for c in chunks if c["heading"] == "GRENADE"]
    assert len(grenade) == 1
    assert "TARGET:" in grenade[0]["text"] and "EFFECT:" in grenade[0]["text"]
    assert all(37 not in c["pages"] for c in chunks)
    assert any(len(c["pages"]) > 1 for c in chunks)
    assert len({c["id"] for c in chunks}) == len(chunks)
    assert all(c["source_sha256"] and c["block_ids"] for c in chunks)


def test_rebuild_and_search_are_deterministic(index):
    path, chunks_path, _ = index
    before = search_rules(path, "grenades")
    build_index(chunks_path, path)
    assert search_rules(path, "grenades") == before


def test_queries_do_not_accept_fts_operators_or_sql(index):
    assert search_rules(index[0], '" OR * ; DROP TABLE rules; --', 2) is not None
    assert search_rules(index[0], "!!!") == []
    assert search_rules(index[0], "zzznosuchrulezzz") == []
    assert search_rules(index[0], "grenades")
    with pytest.raises(ValueError, match="limit"):
        search_rules(index[0], "grenades", 100)


def test_stale_index_is_rejected(index, tmp_path):
    changed = tmp_path / "changed.json"
    changed.write_text("[]")
    with pytest.raises(ValueError, match="stale"):
        search_rules(index[0], "grenades", chunks_path=changed)


def test_exact_unit_stats_and_snapshot_provenance():
    original = hashlib.sha256(DB.read_bytes()).hexdigest()
    result = retrieve_unit(DB, "Intercessor Squad")
    assert result["status"] == "resolved"
    evidence = result["evidence"]
    assert evidence["id"] == "000001157"
    assert evidence["models"][0]["t"] == "4"
    assert evidence["source"] and evidence["snapshot_updated"]
    assert evidence["source_sha256"] == original == hashlib.sha256(DB.read_bytes()).hexdigest()


def test_inline_and_catalog_abilities_do_not_multiply():
    evidence = unit_details(DB, "000000460")
    assert len(evidence["abilities"]) == 6
    names = {a["name"] for a in evidence["abilities"]}
    assert {"Will of the Hive Mind", "Onslaught (Aura, Psychic)", "Synapse"} <= names
    assert all(a["description"] for a in evidence["abilities"])


def test_ambiguous_and_missing_units_are_not_guessed():
    assert retrieve_unit(DB, "Accursed Cultists")["status"] == "ambiguous"
    assert retrieve_unit(DB, "Intercessor")["status"] == "ambiguous"
    assert retrieve_unit(DB, "zzznosuchunitzzz")["status"] == "not_found"
    assert unit_details(DB, "not-an-id") is None
    assert find_units(DB, "%") == []
    assert find_units(DB, "' OR 1=1 --") == []


def test_combined_command_returns_both_sources(index, monkeypatch, capsys):
    monkeypatch.setenv("RAG_PROJECT_ROOT", str(ROOT))
    monkeypatch.setenv("RAG_INDEX_DIR", str(index[0].parent))
    monkeypatch.setenv("RAG_PROCESSED_DIR", str(index[1].parent))
    # CLI uses a fixed index filename, independent of the source database.
    (index[0].parent / "rules.sqlite").write_bytes(index[0].read_bytes())
    assert main(["search", "grenades", "--unit", "Intercessor Squad"]) == 0
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["rules"][0]["pages"] == [42]
    assert evidence["datasheet"]["evidence"]["id"] == "000001157"

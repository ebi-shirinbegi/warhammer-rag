import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf
import pytest

from warhammer_rag.ingestion.rulebook import parse_rulebook

SOURCE = Path(__file__).resolve().parents[1] / "data/raw/core_rules.pdf"


@pytest.fixture(scope="module")
def parsed(tmp_path_factory):
    directory = tmp_path_factory.mktemp("parsed")
    parse_rulebook(SOURCE, directory)
    return json.loads((directory / "core_rules.json").read_text()), directory


def tokens(text):
    return Counter(re.findall(r"\w+", unicodedata.normalize("NFKC", text)))


def test_every_source_word_is_retained_or_has_an_exclusion_reason(parsed):
    artifact, _ = parsed
    assert [p["page"] for p in artifact["pages"]] == list(range(1, 61))
    identifiers = []
    with pymupdf.open(SOURCE) as source:
        for page, record in zip(source, artifact["pages"], strict=True):
            expected = tokens(page.get_text())
            expected.subtract(tokens(" ".join(e["text"] for e in record["excluded"])))
            actual = tokens(" ".join(b["text"] for b in record["blocks"]))
            assert not expected - actual, f"Missing source words on page {page.number + 1}"
            assert all(e["reason"] for e in record["excluded"])
            identifiers.extend(b["id"] for b in record["blocks"])
    assert len(identifiers) == len(set(identifiers))


def test_graphical_wound_and_dice_values_are_preserved(parsed):
    artifact, _ = parsed
    wound = next(b for b in artifact["pages"][20]["blocks"] if b["kind"] == "table")
    assert dict(wound["rows"]) == {
        "S ≥ 2T": "2+",
        "T < S < 2T": "3+",
        "S = T": "4+",
        "T/2 < S < T": "5+",
        "S ≤ T/2": "6+",
    }
    dice = next(b for b in artifact["pages"][8]["blocks"] if b["kind"] == "table")
    assert dice["rows"] == [["1–2", "1"], ["3–4", "2"], ["5–6", "3"]]
    assert wound["provenance"] == dice["provenance"] == "reviewed_source_transcription"


def test_stratagems_retain_costs_and_conditions(parsed):
    artifact, _ = parsed
    cards = {
        b["name"]: b for p in artifact["pages"] for b in p["blocks"] if b["kind"] == "stratagem"
    }
    assert len(cards) == 11
    assert cards["HEROIC INTERVENTION"]["cp_cost"] == 2
    assert cards["COUNTER-OFFENSIVE"]["cp_cost"] == 2
    grenade = cards["GRENADE"]["text"]
    for phrase in (
        "Your Shooting phase",
        "has not been selected to shoot",
        'within 8"',
        "visible",
        "Roll six D6",
        "for each 4+",
        "1 mortal wound",
    ):
        assert phrase in grenade
    assert "once per turn" in cards["FIRE OVERWATCH"]["text"]
    assert "does not receive any Charge bonus" in cards["HEROIC INTERVENTION"]["text"]
    assert "would not normally be able to" in cards["RAPID INGRESS"]["text"]


def test_mission_order_scoring_and_cross_page_scope(parsed):
    artifact, _ = parsed
    mission = artifact["pages"][58]
    headings = [b["text"] for b in mission["blocks"] if b["kind"] == "heading"]
    assert [h[0] for h in headings[1:]] == list("12345")
    text = " ".join(b["text"] for b in mission["blocks"])
    assert "Starting from the second battle round" in text
    assert "at the end of each player’s Command phase" in text
    assert "maximum of 3VP per turn" in text
    assert mission["section_page_range"] == artifact["pages"][59]["section_page_range"] == [59, 60]
    assert artifact["pages"][33]["section_page_range"] == [32, 36]
    assert all(b["example_only"] for b in artifact["pages"][36]["blocks"])


def test_parsing_is_reproducible(parsed, tmp_path):
    _, original = parsed
    parse_rulebook(SOURCE, tmp_path)
    for name in ("core_rules.json", "core_rules.md", "parse_report.json"):
        assert (original / name).read_bytes() == (tmp_path / name).read_bytes()


def test_other_edition_cannot_receive_reviewed_corrections(tmp_path):
    source = tmp_path / "other.pdf"
    source.write_bytes(b"different edition")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="digest differs"):
        parse_rulebook(source, output)
    assert not output.exists()

"""Deterministic, page-addressable extraction of the supplied Core Rules PDF."""

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

import pymupdf

from warhammer_rag.ingestion.profile import CARDS, SECTIONS, SOURCE_SHA256, TABLES, VISUAL_NOTES


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = "".join(c for c in value if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    return re.sub(r"[ \t]+", " ", value).strip()


def inside(bbox: list[float], region: tuple) -> bool:
    x, y = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    return region[0] <= x <= region[2] and region[1] <= y <= region[3]


def native_blocks(page: pymupdf.Page) -> tuple[list[dict], list[dict]]:
    blocks, excluded = [], []
    for raw in page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)["blocks"]:
        lines = []
        for line in raw.get("lines", []):
            text = clean_text("".join(s["text"] for s in line["spans"]))
            if not text:
                continue
            bbox = [round(v, 2) for v in line["bbox"]]
            size = max(s["size"] for s in line["spans"])
            reason = None
            if text.startswith("CORE RULES |") and bbox[1] > 730:
                reason = "running footer"
            elif text.isdecimal() and (bbox[2] < 90 or bbox[0] > 530):
                reason = "margin navigation or page number"
            elif page.number == 3 and size < 8:
                reason = "miniature page thumbnail"
            item = {"text": text, "bbox": bbox, "font_size": round(size, 2)}
            if reason:
                excluded.append({**item, "reason": reason})
            else:
                lines.append(item)
        if lines:
            blocks.append({"lines": lines})
    return blocks, excluded


def combine(lines: list[dict]) -> str:
    """Join wrapped prose, retaining list-item boundaries and printed hyphens."""
    result = ""
    for line in lines:
        text = line["text"].replace("■", "- ")
        separator = " " if result and not result.endswith("-") else ""
        result += ("\n" if text.startswith("- ") and result else separator) + text
    return result.strip()


def make_block(lines: list[dict], kind: str = "paragraph") -> dict:
    bbox = [
        min(line["bbox"][0] for line in lines),
        min(line["bbox"][1] for line in lines),
        max(line["bbox"][2] for line in lines),
        max(line["bbox"][3] for line in lines),
    ]
    text = combine(lines)
    if kind == "paragraph" and text.isupper() and len(text) < 160:
        kind = "heading"
    return {"kind": kind, "text": text, "bbox": bbox, "provenance": "native_pdf_text"}


def table_block(spec: tuple) -> dict:
    bbox, title, columns, rows = spec
    text = title + "\n\n| " + " | ".join(columns) + " |\n"
    text += "| " + " | ".join("---" for _ in columns) + " |\n"
    text += "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return {
        "kind": "table",
        "text": text,
        "bbox": list(bbox),
        "columns": columns,
        "rows": rows,
        "provenance": "reviewed_source_transcription",
    }


def join_list_continuations(blocks: list[dict]) -> list[dict]:
    """Reconnect bullet lines split into overlapping PDF text blocks."""
    result = []
    for block in blocks:
        previous = result[-1] if result else None
        if (
            previous
            and previous["kind"] == block["kind"] == "paragraph"
            and "- " in previous["text"]
            and previous["text"][-1] not in ".:!?"
            and abs(previous["bbox"][0] - block["bbox"][0]) < 3
            and -3 <= block["bbox"][1] - previous["bbox"][3] <= 3
        ):
            previous["text"] += " " + block["text"]
            previous["bbox"][2] = max(previous["bbox"][2], block["bbox"][2])
            previous["bbox"][3] = max(previous["bbox"][3], block["bbox"][3])
        else:
            result.append(block)
    return result


def extract_page(page: pymupdf.Page) -> dict:
    number = page.number + 1
    native, excluded = native_blocks(page)
    cards = CARDS.get(number, [])
    table = TABLES.get(number)
    blocks, card_lines = [], [[] for _ in cards]
    inserted_table = False
    for raw in native:
        kept = []
        for line in raw["lines"]:
            matched = False
            for index, (_, _, region) in enumerate(cards):
                if inside(line["bbox"], region):
                    card_lines[index].append(line)
                    matched = True
                    break
            if matched:
                continue
            if cards and re.fullmatch(r"\d+CP", line["text"]):
                excluded.append({**line, "reason": "cost attached to stratagem record"})
                continue
            if table and inside(line["bbox"], table[0]):
                if kept:
                    blocks.append(make_block(kept))
                    kept = []
                if not inserted_table:
                    blocks.append(table_block(table))
                    inserted_table = True
                excluded.append({**line, "reason": "replaced by reviewed table"})
                continue
            kept.append(line)
        if kept:
            blocks.append(make_block(kept))
    if table and not inserted_table:
        raise ValueError(f"Expected table region missing on page {number}")
    if number == 21:
        # This page's title and introduction occur last in the PDF content stream.
        blocks.sort(key=lambda b: b["bbox"][1] >= 140)
    for (name, cost, _), lines in zip(cards, card_lines, strict=True):
        if not lines or lines[0]["text"] != name:
            raise ValueError(f"Expected stratagem {name} missing on page {number}")
        # Source blocks preserve paragraph boundaries inside each card.
        paragraphs = []
        selected = {tuple(line["bbox"]) for line in lines}
        for raw in native:
            group = [line for line in raw["lines"] if tuple(line["bbox"]) in selected]
            if group:
                paragraphs.append(combine(group))
        block = make_block(lines, "stratagem")
        block.update(name=name, cp_cost=cost, cp_provenance="reviewed_source_transcription")
        block["text"] = f"{name} — {cost}CP\n\n" + "\n\n".join(paragraphs[1:])
        blocks.append(block)
    if number in VISUAL_NOTES:
        blocks.append(
            {
                "kind": "figure_note",
                "text": VISUAL_NOTES[number],
                "bbox": None,
                "provenance": "reviewed_source_transcription",
            }
        )
    blocks = join_list_continuations(blocks)
    start, end, section = next(s for s in SECTIONS if s[0] <= number <= s[1])
    for index, block in enumerate(blocks, 1):
        block["id"] = f"core-rules-p{number:03d}-b{index:03d}"
        block["page"] = number
        block["source_ref"] = f"../raw/core_rules.pdf#page={number}"
        block["example_only"] = number == 37
        block["section_id"] = f"section-{start:03d}"
    return {
        "page": number,
        "section": section,
        "blocks": blocks,
        "excluded": excluded,
        "section_page_range": [start, end],
        "visual_source": f"../raw/core_rules.pdf#page={number}",
        "visual_coverage": "Text and selected reviewed graphics; consult PDF for spatial figures.",
    }


def parse_rulebook(source: Path, output_dir: Path) -> dict:
    """Write Markdown and JSON; reject other editions before applying the layout profile."""
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(
            "Rulebook digest differs from the reviewed edition; review its layout first."
        )
    with pymupdf.open(source) as document:
        if len(document) != 60:
            raise ValueError("Expected the reviewed 60-page rulebook.")
        pages = [extract_page(page) for page in document]
    source_link = Path(os.path.relpath(source.resolve(), output_dir.resolve())).as_posix()
    for page in pages:
        page["visual_source"] = f"{source_link}#page={page['page']}"
        for block in page["blocks"]:
            block["source_ref"] = page["visual_source"]
    artifact = {
        "schema_version": 1,
        "parser": "native-pdf-reviewed-layout-v1",
        "pymupdf_version": pymupdf.VersionBind,
        "source_sha256": digest,
        "source": "data/raw/core_rules.pdf",
        "page_count": len(pages),
        "sections": [
            {"id": f"section-{start:03d}", "title": title, "page_start": start, "page_end": end}
            for start, end, title in SECTIONS
        ],
        "pages": pages,
    }
    markdown = [
        "# Core Rules — parsed rulebook",
        f"Source SHA-256: `{digest}`",
        "Page numbers refer to the supplied PDF. Graphical table transcriptions and "
        "figure notes are identified in the structured artifact. Spatial diagrams remain "
        "available through each page's source link.",
    ]
    for page in pages:
        number = page["page"]
        markdown.append(f"## Page {number} — {page['section']}")
        markdown.append(f"[Source page {number}]({page['visual_source']})")
        if not page["blocks"]:
            markdown.append("*Decorative page; no native text.*")
        for block in page["blocks"]:
            prefix = "### " if block["kind"] in ("heading", "stratagem") else ""
            markdown.append(prefix + block["text"])
    report = {
        "source_sha256": digest,
        "page_count": len(pages),
        "block_count": sum(len(p["blocks"]) for p in pages),
        "stratagem_count": sum(b["kind"] == "stratagem" for p in pages for b in p["blocks"]),
        "reviewed_table_pages": list(TABLES),
        "empty_native_text_pages": [p["page"] for p in pages if not p["blocks"]],
        "limitations": [
            "Spatial illustrations and photographs are linked, not fully interpreted.",
            "Page 37 is an illustrative datasheet, not a live unit profile.",
            "Paragraphs and repeated summaries are retained; retrieval chunking is separate.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (("core_rules.json", artifact), ("parse_report.json", report)):
        (output_dir / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    (output_dir / "core_rules.md").write_text("\n\n".join(markdown) + "\n", encoding="utf-8")
    return report

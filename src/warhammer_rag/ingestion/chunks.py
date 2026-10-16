"""Section-aware chunks with atomic stratagems and source block references."""

import hashlib
import json
from pathlib import Path


def build_chunks(parsed_path: Path, output_path: Path, target_chars: int = 1800) -> list[dict]:
    if target_chars < 200:
        raise ValueError("Chunk target must be at least 200 characters")
    artifact = json.loads(parsed_path.read_text(encoding="utf-8"))
    chunks, pending = [], []
    heading, section = "", ""

    def flush():
        if not pending:
            return
        ids = [block["id"] for block in pending]
        text = "\n\n".join(block["text"] for block in pending)
        if not any(character.isalpha() for character in text):
            pending.clear()
            return
        identity = artifact["source_sha256"] + "|" + "|".join(ids)
        chunks.append(
            {
                "id": "rules-" + hashlib.sha256(identity.encode()).hexdigest()[:16],
                "source_kind": "pdf",
                "source_sha256": artifact["source_sha256"],
                "section": section,
                "heading": heading or section,
                "text": text,
                "pages": sorted({block["page"] for block in pending}),
                "block_ids": ids,
            }
        )
        pending.clear()

    for page in artifact["pages"]:
        if page["page"] <= 4 or page["page"] == 37:
            continue
        if page["section"] != section:
            flush()
            section, heading = page["section"], ""
        for block in page["blocks"]:
            if block["kind"] == "heading":
                flush()
                heading = block["text"]
                continue
            if block["kind"] == "stratagem":
                flush()
                old_heading = heading
                heading = block["name"]
                pending.append(block)
                flush()
                heading = old_heading
                continue
            if pending and sum(len(b["text"]) for b in pending) + len(block["text"]) > target_chars:
                flush()
            pending.append(block)
    flush()
    for position, chunk in enumerate(chunks):
        for field, offset in (("previous_id", -1), ("next_id", 1)):
            neighbor = position + offset
            chunk[field] = None
            if 0 <= neighbor < len(chunks):
                other = chunks[neighbor]
                if (other["section"], other["heading"]) == (chunk["section"], chunk["heading"]):
                    chunk[field] = other["id"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return chunks

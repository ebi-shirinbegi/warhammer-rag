"""Evidence retrieval checks, independent of answer generation and API access."""

import hashlib
import json
from pathlib import Path

from warhammer_rag.retrieval.text import search_rules


def evaluate_retrieval(index: Path, dataset: Path, limit: int = 5) -> dict:
    content = dataset.read_bytes()
    cases = json.loads(content)
    results = []
    for case in cases:
        hits = search_rules(index, case["query"], limit)
        rank = next(
            (
                position
                for position, hit in enumerate(hits, 1)
                if case["page"] in hit["pages"] and case["contains"] in hit["text"]
            ),
            None,
        )
        results.append({"id": case["id"], "rank": rank, "retrieved_ids": [h["id"] for h in hits]})
    return {
        "dataset_sha256": hashlib.sha256(content).hexdigest(),
        "scope": "development retrieval cases; not held-out answer evaluation",
        "k": limit,
        "case_count": len(cases),
        "hit_rate": sum(r["rank"] is not None for r in results) / len(cases) if cases else 0,
        "mean_reciprocal_rank": (
            sum(1 / r["rank"] if r["rank"] else 0 for r in results) / len(cases) if cases else 0
        ),
        "results": results,
    }

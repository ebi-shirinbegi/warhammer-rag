"""Parameterized lookups preserving snapshot identities and raw rule values."""

import hashlib
from pathlib import Path

from warhammer_rag.retrieval.sqlite import readonly_connection


def find_units(database: Path, name: str, limit: int = 10) -> list[dict]:
    if not 1 <= limit <= 20:
        raise ValueError("Result limit must be between 1 and 20")
    if not name.strip():
        return []
    pattern = "%" + name.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    with readonly_connection(database) as connection:
        rows = connection.execute(
            "SELECT Id, name, factionId, sourceId FROM datasheets "
            "WHERE name LIKE ? ESCAPE '\\' "
            "ORDER BY (lower(name) = lower(?)) DESC, name, Id LIMIT ?",
            (pattern, name.strip(), limit),
        ).fetchall()
    return [dict(row) for row in rows]


def unit_details(database: Path, unit_id: str) -> dict | None:
    with readonly_connection(database) as connection:
        # Guard static relation lookups against unexpectedly expensive replacement snapshots.
        connection.set_progress_handler(lambda: 1, 2_000_000)
        unit = connection.execute("SELECT * FROM datasheets WHERE Id = ?", (unit_id,)).fetchone()
        if unit is None:
            return None
        source = connection.execute(
            "SELECT * FROM source WHERE Id = ?", (unit["sourceId"],)
        ).fetchone()
        result = {
            "source_kind": "sqlite",
            "table": "datasheets",
            "id": unit_id,
            "source_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
            "unit": dict(unit),
            "source": dict(source) if source else None,
        }
        for table, key in (
            ("datasheets_models", "models"),
            ("datasheets_models_cost", "costs"),
            ("datasheets_keywords", "keywords"),
        ):
            order = "CAST(line AS INTEGER)" if key != "keywords" else "keyword, model"
            result[key] = [
                dict(r)
                for r in connection.execute(
                    f"SELECT DISTINCT * FROM {table} WHERE DatasheetId = ? ORDER BY {order}",
                    (unit_id,),
                )
            ]
        result["abilities"] = [
            dict(r)
            for r in connection.execute(
                "SELECT da.line, da.type, da.abilityId, da.model, da.parameter, "
                "COALESCE(NULLIF(da.name, ''), a.name) AS name, "
                "COALESCE(NULLIF(da.description, ''), a.description) AS description "
                "FROM datasheets_abilities da LEFT JOIN abilities a ON a.Id = da.abilityId "
                "AND (a.factionId = ? OR a.factionId = '') WHERE da.DatasheetId = ? "
                "ORDER BY CAST(da.line AS INTEGER)",
                (unit["factionId"], unit_id),
            )
        ]
        result["snapshot_updated"] = connection.execute(
            "SELECT LastUpdate FROM last_update LIMIT 1"
        ).fetchone()[0]
    return result


def retrieve_unit(database: Path, name: str) -> dict:
    candidates = find_units(database, name)
    exact = [c for c in candidates if c["name"].casefold() == name.strip().casefold()]
    if len(exact) == 1:
        return {"status": "resolved", "evidence": unit_details(database, exact[0]["Id"])}
    return {"status": "ambiguous" if candidates else "not_found", "candidates": candidates}

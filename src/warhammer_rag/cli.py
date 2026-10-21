"""Offline configuration and source-data diagnostics."""

import argparse
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from warhammer_rag.config import Settings
from warhammer_rag.retrieval.sqlite import readonly_connection


def doctor(settings: Settings, *, require_api_key: bool = False) -> int:
    """Check local inputs; report credential presence without exposing it."""
    print(f"Project: {settings.project_root}")
    failures = 0
    for label, path in (("Rulebook", settings.rulebook_path), ("SQLite", settings.database_path)):
        exists = path.is_file()
        print(f"{'OK' if exists else 'MISSING'} {label}: {path}")
        failures += int(not exists)
    if settings.database_path.is_file():
        try:
            with readonly_connection(settings.database_path) as connection:
                count = connection.execute(
                    "SELECT COUNT(*) FROM sqlite_schema WHERE type = 'table'"
                ).fetchone()[0]
            print(f"OK read-only database connection ({count} tables)")
        except (OSError, sqlite3.Error):
            print("ERROR database could not be read as SQLite")
            failures += 1
    print(f"GOOGLE_API_KEY: {'configured' if settings.has_api_key else 'not configured'}")
    print(f"GOOGLE_MODEL: {'configured' if settings.google_model else 'not configured'}")
    if require_api_key and not settings.has_api_key:
        print("ERROR configure GOOGLE_API_KEY locally in .env")
        failures += 1
    print("No API call was made.")
    return int(failures > 0)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="warhammer-rag",
        description="Warhammer RAG command-line utilities.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "doctor", help="Check local inputs and configuration without API calls"
    )
    check.add_argument(
        "--require-api-key", action="store_true", help="Fail if GOOGLE_API_KEY is missing"
    )
    parse = commands.add_parser("parse", help="Parse the supplied Core Rules PDF offline")
    parse.add_argument("--output-dir", type=Path, help="Override the parsed artifact directory")
    commands.add_parser("check-api", help="Make one small Gemini request to test API access")
    commands.add_parser("index", help="Build rulebook chunks and the offline search index")
    commands.add_parser("evaluate-retrieval", help="Run the offline retrieval development cases")
    generate = commands.add_parser(
        "generate-eval", help="Generate a draft text benchmark via Gemini"
    )
    generate.add_argument("--output", type=Path, default=Path("evaluation/datasets/text.json"))
    evaluate = commands.add_parser(
        "evaluate-answers", help="Run or resume model-judged text evaluation"
    )
    evaluate.add_argument("--dataset", type=Path, default=Path("evaluation/datasets/text.json"))
    evaluate.add_argument("--output", type=Path, default=Path("evaluation/reports/answers.json"))
    evaluate.add_argument("--limit", type=int, help="Evaluate only the first N cases")
    search = commands.add_parser("search", help="Retrieve rulebook and optional unit evidence")
    search.add_argument("query")
    search.add_argument("--unit", help="Unit name to look up in SQLite")
    search.add_argument("--limit", type=int, default=5)
    units = commands.add_parser("units", help="Find unit names and exact datasheet IDs")
    units.add_argument("name")
    unit = commands.add_parser("unit", help="Retrieve a datasheet by its exact ID")
    unit.add_argument("id")
    chat = commands.add_parser("chat", help="Open the local Warhammer chat server")
    chat.add_argument("--port", type=int, default=8000)
    chat.add_argument("--no-browser", action="store_true", help="Do not open the default browser")
    args = parser.parse_args(argv)
    try:
        settings = Settings()
    except ValidationError:
        # Do not print validation details, which may contain raw environment values.
        parser.exit(2, "Invalid configuration. Check the paths and values in .env.\n")
    if args.command in {"generate-eval", "evaluate-answers"}:
        from warhammer_rag.evaluation.answers import evaluate_answers, generate_dataset

        try:
            if args.command == "generate-eval":
                result = generate_dataset(settings, args.output)
                print(f"Generated {len(result['cases'])} draft cases: {args.output}")
                print("Review every reference against its evidence before evaluation.")
            else:
                if args.limit is not None and args.limit < 1:
                    raise ValueError("Limit must be positive.")
                print(
                    json.dumps(
                        evaluate_answers(settings, args.dataset, args.output, args.limit), indent=2
                    )
                )
            return 0
        except Exception as exc:
            print(
                f"Evaluation failed ({type(exc).__name__}). Check configuration, dataset review "
                "and saved run metadata. Existing checkpoints are retained."
            )
            return 1
    if args.command == "chat":
        from warhammer_rag.web.server import serve

        return serve(settings, args.port, launch_browser=not args.no_browser)
    if args.command in {"index", "search", "units", "unit", "evaluate-retrieval"}:
        from warhammer_rag.ingestion.chunks import build_chunks
        from warhammer_rag.retrieval.datasheets import find_units, retrieve_unit, unit_details
        from warhammer_rag.retrieval.text import build_index, search_rules

        try:
            index_path = settings.index_dir / "rules.sqlite"
            if args.command == "evaluate-retrieval":
                from warhammer_rag.evaluation.retrieval import evaluate_retrieval

                result = evaluate_retrieval(index_path, settings.eval_dir / "retrieval.json")
                settings.report_dir.mkdir(parents=True, exist_ok=True)
                (settings.report_dir / "retrieval.json").write_text(
                    json.dumps(result, indent=2) + "\n", encoding="utf-8"
                )
                print(json.dumps(result, indent=2))
                return int(result["hit_rate"] < 1)
            if args.command == "index":
                chunks_path = settings.processed_dir / "chunks.json"
                build_chunks(settings.processed_dir / "core_rules.json", chunks_path)
                count = build_index(chunks_path, index_path)
                print(f"Indexed {count} chunks: {index_path}")
                return 0
            if args.command == "search":
                result = {
                    "rules": search_rules(
                        index_path,
                        args.query,
                        args.limit,
                        chunks_path=settings.processed_dir / "chunks.json",
                    )
                }
                if args.unit:
                    result["datasheet"] = retrieve_unit(settings.database_path, args.unit)
            elif args.command == "units":
                result = find_units(settings.database_path, args.name)
            else:
                result = unit_details(settings.database_path, args.id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        except (OSError, ValueError, sqlite3.Error) as exc:
            print(f"ERROR {exc}")
            return 1
    if args.command == "check-api":
        from google.genai.errors import APIError

        from warhammer_rag.chat.gemini import check_connection

        try:
            success = check_connection(settings)
        except ValueError:
            print("ERROR configure GOOGLE_API_KEY and GOOGLE_MODEL in .env.")
            return 1
        except APIError as exc:
            print(f"ERROR Gemini request failed (HTTP {exc.code}).")
            return 1
        except Exception:
            # Transport exceptions may include request URLs; never print their payloads.
            print("ERROR Gemini connection failed. Check network access and configuration.")
            return 1
        print("OK Gemini connection" if success else "ERROR unexpected or empty Gemini response")
        return int(not success)
    if args.command == "parse":
        from warhammer_rag.ingestion.rulebook import parse_rulebook

        try:
            report = parse_rulebook(
                settings.rulebook_path, args.output_dir or settings.processed_dir
            )
        except (OSError, ValueError) as exc:
            print(f"ERROR {exc}")
            return 1
        print(f"Parsed {report['page_count']} pages, {report['stratagem_count']} stratagems.")
        print(f"Output: {args.output_dir or settings.processed_dir}")
        return 0
    return doctor(settings, require_api_key=args.require_api_key)

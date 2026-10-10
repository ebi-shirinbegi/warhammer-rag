from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from docling_parser import parse_document


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse a document with Docling")
    parser.add_argument("document", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    markdown = parse_document(args.document, args.output)
    if args.output is None:
        print(markdown)
    else:
        print(f"Wrote parsed document to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

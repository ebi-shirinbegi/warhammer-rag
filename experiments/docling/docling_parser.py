from __future__ import annotations

from pathlib import Path

from docling.document_converter import DocumentConverter


def parse_document(document_path: str | Path, output_path: str | Path | None = None) -> str:
    converter = DocumentConverter()
    result = converter.convert(str(document_path))
    markdown = result.document.export_to_markdown()

    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown, encoding="utf-8")

    return markdown

# Warhammer RAG Project

This project implements a LangChain retrieval augmented generation assistant
for Warhammer 40,000. It combines the Core Rules PDF with the unit datasheet
SQLite database so users can ask rulebook questions, database questions, and
questions requiring both sources.

The project contains separate PDF parsing, text retrieval, SQLite retrieval,
chat, and evaluation modules. Docling is used for PDF parsing, and Google AI
Studio provides the language model.

## Sources

- `data/Core Rules.pdf`
- `data/wahadb.sqlite`
- `data/SQL_AGENT_DATA_DICTIONARY.md`

## Setup

```bash
source .venv/bin/activate
pip install -e .
```

Add the Google AI Studio key to a local `.env` file using `.env.example` as a
template. Tests will be run with `pytest`, and code quality checks with `ruff`.

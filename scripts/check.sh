#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
./scripts/uv run --locked ruff check .
./scripts/uv run --locked ruff format --check .
./scripts/uv run --locked pytest
./scripts/uv run --locked warhammer-rag doctor

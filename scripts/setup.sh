#!/bin/sh
# Bootstrap isolated tooling; does not change shell profiles or system Python.
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
if [ ! -x .tools/uv/bin/uv ]; then
    python3 -m venv .tools/uv
    .tools/uv/bin/python -m pip install 'uv==0.13.0'
fi
./scripts/uv sync --locked
if [ -d .git ]; then
    ./scripts/uv run --locked pre-commit install
fi
./scripts/uv run --locked warhammer-rag doctor

#!/usr/bin/env bash
set -e
venv/bin/isort .
venv/bin/black .
venv/bin/ruff check .
venv/bin/isort . --check-only
venv/bin/black . --check
tools/smoke_imports.sh
echo "QA OK"


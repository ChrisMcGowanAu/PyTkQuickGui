#!/usr/bin/env bash
# Lint, format-check and import-check the whole tree.  The tools live in the
# venv (see requirments.txt).  Config: .flake8 and pyproject.toml.
set -e
venv/bin/isort .
venv/bin/black .
venv/bin/ruff check .
venv/bin/flake8 $(git ls-files '*.py')
venv/bin/isort . --check-only
venv/bin/black . --check
tools/smoke_imports.sh
echo "QA OK"


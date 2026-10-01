#!/usr/bin/env bash
# Lint, format-check and import-check the tracked tree.  The tools live in the
# venv (see requirments.txt).  Config: .flake8 and pyproject.toml.
# Only tracked files are touched, so untracked scratch files are left alone.
set -e
FILES=$(git ls-files '*.py')
venv/bin/isort $FILES
venv/bin/black $FILES
venv/bin/ruff check $FILES
venv/bin/flake8 $FILES
venv/bin/isort --check-only $FILES
venv/bin/black --check $FILES
tools/smoke_imports.sh
echo "QA OK"

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
# The same disable list the Pylint workflow uses, read from the workflow, so
# qa.sh cannot pass while CI fails (it did once: pylint finds name shadowing
# that flake8 and ruff do not).
venv/bin/pylint --disable=$(grep -oE 'pylint --disable=[^ ]+' .github/workflows/pylint.yml | sed 's/pylint --disable=//') $FILES
tools/smoke_imports.sh
# the projects we ship: generated and built, so they cannot rot silently
venv/bin/python tools/smoke_flet_generated.py "examples/*/*.json"
echo "QA OK"

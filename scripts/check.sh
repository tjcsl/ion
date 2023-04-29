#!/bin/bash
# Convenience script that runs format and lint scripts.

set -e

echo "Formatting..."
./scripts/format.sh
./scripts/static_templates_format.sh
echo

echo "Building sources..."
./scripts/build_sources.sh
echo

echo "Validating commit messages..."
./scripts/validate-commit-messages.py $(git rev-parse HEAD~1)
echo

if [ "$1" = "--lint" ]; then
    echo "Linting..."
    ./scripts/lint.sh
    echo
fi

echo "Done!"
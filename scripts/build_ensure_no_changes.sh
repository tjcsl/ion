#!/bin/bash
"$@"
if [ -n "$(git status --porcelain=v1)" ]; then
    echo "Modified files found, did you forget to run scripts/update_docs_sources.sh?"
    git status --porcelain=v1
    exit 1
fi

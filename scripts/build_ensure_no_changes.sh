#!/bin/bash
"$@"
if [ -n "$(git status --porcelain=v1)" ]; then
    echo "Modified files found, did you forget to run '$@'?"
    git status --porcelain=v1
    exit 1
fi

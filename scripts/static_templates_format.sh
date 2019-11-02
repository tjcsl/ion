#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f -- "$0")")")"

# Remove trailing whitespace for all JS/CSS/SCSS/txt/JSON/SVG static files
find intranet/static -name vendor -prune -o -type f '(' -name '*.js' -o -name '*.css' -o -name '*.scss' -o -name '*.txt' -o -name '*.json' -o -name '*.svg' ')' -exec sed -i 's/\s\+$//' '{}' ';'
# Remove trailing whitespace for all templates
find intranet/templates -type f -exec sed -i 's/\s\+$//' '{}' ';'

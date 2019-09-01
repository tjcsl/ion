#!/bin/bash
cd "$(dirname -- "$(readlink -f -- "$0")")/.."
./scripts/build_docs.sh
./scripts/build_sources.sh

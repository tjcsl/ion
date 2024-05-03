#!/bin/bash

# This script is now obsolete due to the use of pyproject.toml. It is kept for future reference.
cd "$(dirname -- "$(readlink -f -- "$0")")/.."
./setup.py egg_info

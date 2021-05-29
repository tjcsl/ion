#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

black . && autopep8 --in-place --recursive . && isort .

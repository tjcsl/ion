#!/bin/bash
cd "$(dirname -- "$(dirname -- "$(readlink -f "$0")")")"

black intranet && autopep8 --in-place --recursive intranet && isort --recursive intranet

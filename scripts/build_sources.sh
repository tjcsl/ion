#!/bin/bash
cd "$(dirname -- "$(readlink -f -- "$0")")/.."
./setup.py egg_info

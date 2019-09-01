#!/bin/bash
cd "$(dirname -- "$(readlink -f -- "$0")")/.."
exec ./setup.py egg_info

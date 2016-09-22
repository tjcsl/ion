#!/bin/bash
export MYPYPATH=intranet/test/stubs
echo "Checking static types..."
mypy --incremental intranet

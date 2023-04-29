#!/bin/bash

flake8 --max-line-length 150 --exclude=*/migrations/* intranet/ scripts/ docs/ *.py
pylint --jobs=8 --disable=fixme,broad-exception-caught,broad-exception-raised,unsupported-binary-operation,global-statement,attribute-defined-outside-init,cyclic-import,consider-using-f-string --django-settings-module=intranet.settings intranet/

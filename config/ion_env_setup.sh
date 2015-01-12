#!/bin/bash

# Virtualenv/Pip config
export VIRTUALENV_DISTRIBUTE=true
export PIP_VIRTUALENV_BASE=~/.virtualenvs
export WORKON_HOME=~/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python
export PIP_DOWNLOAD_CACHE=~/.virtualenvs/cache
source /usr/local/bin/virtualenvwrapper.sh

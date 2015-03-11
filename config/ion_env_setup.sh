#!/bin/bash

# Virtualenv/Pip config
export VIRTUALENV_DISTRIBUTE=true
export PIP_VIRTUALENV_BASE=~/.virtualenvs
export WORKON_HOME=~/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python
source /usr/local/bin/virtualenvwrapper.sh

export PATH=$PATH:/usr/lib/postgresql/9.3/bin

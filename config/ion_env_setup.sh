#!/bin/bash

# Virtualenv/Pip config
export VIRTUALENV_DISTRIBUTE=true
export PIP_VIRTUALENV_BASE=~/.virtualenvs
export WORKON_HOME=~/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh

export PATH=$PATH:/usr/lib/postgresql/9.3/bin

function devconfig() {
    python3 -c "
import json
f = open('/home/vagrant/intranet/config/devconfig.json', 'r')
print(json.load(f)['$1'])
f.close()"
}

export PGUSER="ion"
export PGPASSWORD="$(devconfig sql_password)"

from __future__ import with_statement
from fabric.api import *

def clean_pyc():
    local("find . -name '*.pyc' -delete")

def runserver(port=None, dbt="yes"):
    if not port:
        abort("You must specify a port.")

    clean_pyc()

    if dbt.lower() not in ("yes", "no"):
        abort("Specify 'yes' or 'no' for 'dbt' option (enable debug toolbar.)")

    with shell_env(SHOW_DEBUG_TOOLBAR=dbt.upper()):
        local("./manage.py runserver 0.0.0.0:{}".format(port))

from __future__ import with_statement
from fabric.api import *

def clean_pyc():
    local("find . -name '*.pyc' -delete")

def runserver(port=None):
    if not port:
        abort("You must specify a port.")
    clean_pyc()
    local("./manage.py runserver 0.0.0.0:{}".format(port))

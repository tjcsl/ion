from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
# from fabric.operations.prompt
import os

PRODUCTION_DOCUMENT_ROOT = "/usr/local/www/intranet3"
REDIS_SESSION_DB = 0
REDIS_PRODUCTION_CACHE_DB = 1
REDIS_SANDBOX_CACHE_DB = 2


def _choose_from_list(options, question):
    message = ""
    for index, value in enumerate(options):
        message += "[{}] {}\n".format(index, value)
    message += "\n" + question

    def valid(n):
        if int(n) not in range(len(options)):
            raise ValueError("Not a valid option.")
        else:
            return True

    prompt(message, validate=valid)

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


def _require_root():
    with hide('running'):
        if local('whoami', capture=True) != "root":
            abort("You must be root.")


def clean_production_pyc():
    _require_root()
    with lcd(PRODUCTION_DOCUMENT_ROOT):
        clean_pyc()


def restart_production_gunicorn():
    _require_root()
    with hide('running'):
        if local('whoami', capture=True) != "root":
            abort("You must be root.")
    if confirm("Are you sure you want to restart the production?"
               "Gunicorn instance?"):

        local("supervisorctl reload")


def clear_sessions():
    if "VIRTUAL_ENV" in os.environ:
        ve = os.path.basename(os.environ['VIRTUAL_ENV'])
    else:
        ve = ""

    ve = prompt("Enter the name of the "
                "sandbox whose sessions you would like to delete, or "
                "\"ion\" to clear production sessions:",
                default=ve)

    c = "redis-cli -n {0} KEYS {1}:session:* | sed 's/\"^.*\")//g'"
    keys_command = c.format(REDIS_SESSION_DB, ve)

    keys = local(keys_command, capture=True)
    count = 0 if keys.strip() == "" else keys.count("\n") + 1

    if count == 0:
        print("No sessions to destroy.")
        return 0

    plural = "s" if count != 1 else ""


    if not confirm("Are you sure you want to destroy {} {}"
                   "session{}?".format(count,
                                       "production " if ve == "ion" else "",
                                       plural)):
        return 0

    if count > 0:
        local("{0}| xargs redis-cli -n "
              "{1} DEL".format(keys_command, REDIS_SESSION_DB))

        print("Destroyed {} session{}.".format(count, plural))


def clear_cache():
    n = _choose_from_list(["Production cache",
                           "Sandbox cache"],
                          "Which cache would you like to clear?")
    if n == 0:
        local("redis-cli -n {} FLUSHDB".format(REDIS_PRODUCTION_CACHE_DB))
    else:
        local("redis-cli -n {} FLUSHDB".format(REDIS_SANDBOX_CACHE_DB))

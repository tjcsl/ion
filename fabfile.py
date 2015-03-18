# -*- coding: utf-8 -*-
from __future__ import unicode_literals, with_statement

from fabric.api import *
from fabric.contrib.console import confirm
import os

PRODUCTION_DOCUMENT_ROOT = "/usr/local/www/intranet3"
REDIS_SESSION_DB = 0
REDIS_PRODUCTION_CACHE_DB = 1
REDIS_SANDBOX_CACHE_DB = 2


def _choose_from_list(options, question):
    """Choose an item from a list."""
    message = ""
    for index, value in enumerate(options):
        message += "[{}] {}\n".format(index, value)
    message += "\n" + question

    def valid(n):
        if int(n) not in range(len(options)):
            raise ValueError("Not a valid option.")
        else:
            return int(n)

    prompt(message, validate=valid, key="answer")
    return env.answer


def clean_pyc():
    """Clean .pyc files in the current directory."""
    local("find . -name '*.pyc' -delete")


def runserver(port=8080,
              debug_toolbar="yes",
              werkzeug="no",
              dummy_cache="no",
              short_cache="no",
              warn_invalid_template_vars="no",
              log_level="DEBUG"):
    """Clear compiled python files and start the Django dev server."""
    if not port or (not isinstance(port, int) and not port.isdigit()):
        abort("You must specify a port.")

    clean_pyc()

    yes_or_no = ("debug_toolbar",
                 "werkzeug",
                 "dummy_cache",
                 "short_cache",
                 "warn_invalid_template_vars")
    for arg, name in [(locals()[s].lower(), s) for s in yes_or_no]:
        if arg not in ("yes", "no"):
            abort("Specify 'yes' or 'no' for '" + name + "' option.")

    _log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    if log_level not in _log_levels:
        abort("Invalid log level.")

    with shell_env(SHOW_DEBUG_TOOLBAR=debug_toolbar.upper(),
                   DUMMY_CACHE=dummy_cache.upper(),
                   SHORT_CACHE=short_cache.upper(),
                   WARN_INVALID_TEMPLATE_VARS=warn_invalid_template_vars.upper(),
                   LOG_LEVEL=log_level):
        local("./manage.py runserver{} 0.0.0.0:{}".format("_plus" if werkzeug.lower() == "yes" else "", port))


def kill_server(port):
    """Kill the Django development server currently running on a port."""
    try:
        int(port)
    except ValueError:
        abort("Invalid port number.")
    local("ps au | grep virtualenvs | grep {} | grep -v grep | cut -d' ' -f2 | xargs kill -9".format(port))


def _require_root():
    """Check if running as root."""
    with hide('running'):
        if local('whoami', capture=True) != "root":
            abort("You must be root.")


def clean_production_pyc():
    """Clean production .pyc files."""
    _require_root()
    with lcd(PRODUCTION_DOCUMENT_ROOT):
        clean_pyc()


def restart_production_gunicorn(skip=False):
    """Restart the production gunicorn instance as root."""
    _require_root()

    if skip or confirm("Are you sure you want to restart the production "
                       "Gunicorn instance?"):
        clean_production_pyc()
        local("supervisorctl restart ion")


def clear_sessions(venv=None):
    """Clear all sessions for all sandboxes or for production."""
    if "VIRTUAL_ENV" in os.environ:
        ve = os.path.basename(os.environ["VIRTUAL_ENV"])
    else:
        ve = ""

    if venv is not None:
        ve = venv
    else:
        ve = prompt("Enter the name of the "
                    "sandbox whose sessions you would like to delete, or "
                    "\"ion\" to clear production sessions:",
                    default=ve)

    c = "redis-cli -n {0} KEYS {1}:session:* | sed 's/\"^.*\")//g'"
    keys_command = c.format(REDIS_SESSION_DB, ve)

    keys = local(keys_command, capture=True)
    count = 0 if keys.strip() == "" else keys.count("\n") + 1

    if count == 0:
        puts("No sessions to destroy.")
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

        puts("Destroyed {} session{}.".format(count, plural))


def clear_cache(input=None):
    """Clear the production or sandbox redis cache."""
    if input is not None:
        n = input
    else:
        n = _choose_from_list(["Production cache",
                               "Sandbox cache"],
                              "Which cache would you like to clear?")

    if n == 0:
        local("redis-cli -n {} FLUSHDB".format(REDIS_PRODUCTION_CACHE_DB))
    else:
        local("redis-cli -n {} FLUSHDB".format(REDIS_SANDBOX_CACHE_DB))


def contributors():
    """Print a list of contributors through git."""
    with hide('running'):
        local("git --no-pager shortlog -ns")


def linecount():
    """Get a total line count of files with these types:"""
    with hide("running"):
        local("cloc --exclude-ext=json --exclude-dir=intranet/static/vendor,intranet/static/{css,js}/vendor,docs,intranet/apps/{eighth,schedule,announcements,users}/migrations .")


def load_fixtures():
    """Populate a database with data from fixtures."""

    if local("pwd", capture=True) == PRODUCTION_DOCUMENT_ROOT:
        abort("Refusing to automatically load "
              "fixtures into production database")

    if not confirm("Are you sure you want to load all fixtures? This could "
                   "have unintended consequences if the database "
                   "is not empty."):
            abort("Aborted.")

    files = ["fixtures/users/users.json",
             "fixtures/eighth/sponsors.json",
             "fixtures/eighth/rooms.json",
             "fixtures/eighth/blocks.json",
             "fixtures/eighth/activities.json",
             "fixtures/eighth/scheduled_activities.json",
             "fixtures/eighth/signups.json",
             "fixtures/announcements/announcements.json"]

    for f in files:
        local("./manage.py loaddata " + f)


def deploy():
    """Deploy to production."""
    _require_root()
    obnoxious_mode = True

    if obnoxious_mode:
        # TODO: ensure the build is green
        if not confirm("Are you sure you want to deploy?"):
            abort("Aborted.")
        if not confirm("This will kill all active sessions. Are you still sure?"):
            abort("Aborted.")
        if not confirm("Has the database been migrated?"):
            abort("Aborted.")
        if not confirm("Are you absolutely sure you want to deploy? This is your last chance to stop the deployment"):
            abort("Aborted.")

    with lcd(PRODUCTION_DOCUMENT_ROOT):
        with shell_env(PRODUCTION="TRUE"):
            local("git pull")
            clear_sessions("ion")
            clear_cache(0)
            with prefix("source /usr/local/virtualenvs/ion/bin/activate"):
                local("./manage.py collectstatic")
            restart_production_gunicorn(True)

    puts("Deploy complete!")

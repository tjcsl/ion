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
    """
      Choose an item from a list.
    """
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
    """
      Clean .pyc files in the current directory.
    """
    local("find . -name '*.pyc' -delete")


def runserver(port=None, dbt="yes"):
    """
      Start the Django development testing server through manage.py runserver
    """
    if not port:
        abort("You must specify a port.")

    clean_pyc()

    if dbt.lower() not in ("yes", "no"):
        abort("Specify 'yes' or 'no' for 'dbt' option (enable debug toolbar.)")

    with shell_env(SHOW_DEBUG_TOOLBAR=dbt.upper()):
        local("./manage.py runserver 0.0.0.0:{}".format(port))


def killserver(port):
    """
      Kill the currently running Django development server.
    """
    try:
        int(port)
    except ValueError:
        abort("Not a valid port number.")

    local("pgrep -f 'runserver 0.0.0.0:{}'|xargs kill -INT".format(port))


def _require_root():
    """
      Check if running as root.
    """
    with hide('running'):
        if local('whoami', capture=True) != "root":
            abort("You must be root.")


def clean_production_pyc():
    """
      Clean .pyc files as root.
    """
    _require_root()
    with lcd(PRODUCTION_DOCUMENT_ROOT):
        clean_pyc()


def restart_production_gunicorn():
    """
      Restart the production gunicorn instance as root.
    """
    _require_root()
    with hide('running'):
        if local('whoami', capture=True) != "root":
            abort("You must be root.")
    if confirm("Are you sure you want to restart the production?"
               "Gunicorn instance?"):

        local("supervisorctl reload")


def clear_sessions():
    """
      Clear all sessions in a sandbox or production.
    """
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


def clear_cache():
    """
      Clear the production or sandbox redis cache.
    """
    n = _choose_from_list(["Production cache",
                           "Sandbox cache"],
                          "Which cache would you like to clear?")
    if n == 0:
        local("redis-cli -n {} FLUSHDB".format(REDIS_PRODUCTION_CACHE_DB))
    else:
        local("redis-cli -n {} FLUSHDB".format(REDIS_SANDBOX_CACHE_DB))


def contributors():
    """
      See a list of contributors through git.
    """
    with hide('running'):
        local("git --no-pager shortlog -ns")


def linecount():
    """
      Get a total line count of files with these types:
        * Python
        * HTML
        * CSS
        * Javascript
        * reST documentation
    """
    with hide('running'):
        extensions = [("py", "Python"),
                      ("html", "HTML"),
                      ("css", "CSS"),
                      ("js", "Javascript"),
                      ("rst", "reST documentation")]
        count = [0] * len(extensions)

        for i, e in enumerate(extensions):
            count[i] = int(local("find . -not -iwholename '*.git*' -not "
                                 "-iwholename '*_build*' -name '*.{}' "
                                 "| xargs wc -l | tail -1 | "
                                 "awk '{{print $1;}}'".format(e[0]),
                                 capture=True))
        puts("")

        total = sum(count)

        for i, c in enumerate(count):
            puts("{}{} lines of {} ({:.2f}%)".format(" " * (7 + 8 - len(str(c))), c, extensions[i][1], 100.0 * c / total))

        puts("-" * 52)
        puts("Total: {}{}".format(" " * (8 - len(str(total))), total))


def load_fixtures():
    """
      Clear and repopulate either the production or sandbox
      database with filler data as defined in fixtures.
    """
    n = _choose_from_list(["Production database (PostgreSQL)",
                           "Sandbox database (SQLite3)"],
                          "Which database would you like to clear and repopulate?")
    if n == 0:
        if not confirm("Are you sure you want to clear the production database?"):
            return 0
        production = "TRUE"
        local("dropdb -h localhost ion")
        local("createdb -h localhost ion")
    else:
        production = "FALSE"
        with settings(warn_only=True):
            local("rm testing_database.db")

    with shell_env(PRODUCTION=production):
        local("./manage.py syncdb")
        files = ["intranet/apps/users/fixtures/users.json",
                 "intranet/apps/eighth/fixtures/sponsors.json",
                 "intranet/apps/eighth/fixtures/rooms.json",
                 "intranet/apps/eighth/fixtures/blocks.json",
                 "intranet/apps/eighth/fixtures/activities.json",
                 "intranet/apps/eighth/fixtures/s_activities.json",
                 "intranet/apps/eighth/fixtures/signups_0.json",
                 "intranet/apps/announcements/fixtures/announcements.json"]
        for json_fi
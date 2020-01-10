import os
import traceback

from fabric.api import abort, env, hide, lcd, local, prefix, prompt, puts, shell_env
from fabric.contrib.console import confirm

import pkg_resources

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


def runserver(
    port=8080, debug_toolbar="yes", werkzeug="no", dummy_cache="no", short_cache="no", template_warnings="no", log_level="DEBUG", insecure="no"
):
    """Clear compiled python files and start the Django dev server."""
    if not port or (not isinstance(port, int) and not port.isdigit()):
        abort("You must specify a port.")

    # clean_pyc()
    yes_or_no = ("debug_toolbar", "werkzeug", "dummy_cache", "short_cache", "template_warnings", "insecure")
    for s in yes_or_no:
        if locals()[s].lower() not in ("yes", "no"):
            abort("Specify 'yes' or 'no' for {} option.".format(s))

    _log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    if log_level not in _log_levels:
        abort("Invalid log level.")

    with shell_env(
        SHOW_DEBUG_TOOLBAR=debug_toolbar.upper(),
        DUMMY_CACHE=dummy_cache.upper(),
        SHORT_CACHE=short_cache.upper(),
        WARN_INVALID_TEMPLATE_VARS=template_warnings.upper(),
        LOG_LEVEL=log_level,
    ):
        local(
            "./manage.py runserver{} 0.0.0.0:{}{}".format(
                "_plus" if werkzeug.lower() == "yes" else "", port, " --insecure" if insecure.lower() == "yes" else ""
            )
        )


def killserver():
    """Kills all Django development servers."""
    local("ps xf | grep runserver | grep -v grep | cut -d' ' -f1 | xargs kill -9")


def _require_root():
    """Check if running as root."""
    with hide("running"):
        if local("whoami", capture=True) != "root":
            abort("You must be root.")


def clean_production_pyc():
    """Clean production .pyc files."""
    _require_root()
    with lcd(PRODUCTION_DOCUMENT_ROOT):
        clean_pyc()


def restart_production_gunicorn(skip=False):
    """Restart the production gunicorn instance as root."""
    _require_root()

    if skip or confirm("Are you sure you want to restart the production " "Gunicorn instance?"):
        clean_production_pyc()
        local("supervisorctl restart ion:*")


def clear_sessions(venv=None):
    """Clear all sessions for all sandboxes or for production."""
    if "VIRTUAL_ENV" in os.environ:
        ve = os.path.basename(os.environ["VIRTUAL_ENV"])
    else:
        ve = ""

    if venv is not None:
        ve = venv
    else:
        ve = prompt("Enter the name of the " "sandbox whose sessions you would like to delete, or " '"ion" to clear production sessions:', default=ve)

    c = "redis-cli -n {0} KEYS {1}:session:* | sed 's/\"^.*\")//g'"
    keys_command = c.format(REDIS_SESSION_DB, ve)

    keys = local(keys_command, capture=True)
    count = 0 if keys.strip() == "" else keys.count("\n") + 1

    if count == 0:
        puts("No sessions to destroy.")
        return 0

    plural = "s" if count != 1 else ""

    if not confirm("Are you sure you want to destroy {} {}" "session{}?".format(count, "production " if ve == "ion" else "", plural)):
        return 0

    if count > 0:
        local("{0}| xargs redis-cli -n " "{1} DEL".format(keys_command, REDIS_SESSION_DB))

        puts("Destroyed {} session{}.".format(count, plural))


def clear_cache(input=None):
    """Clear the production or sandbox redis cache."""
    if input is not None:
        n = input
    else:
        n = _choose_from_list(["Production cache", "Sandbox cache"], "Which cache would you like to clear?")

    if n == 0:
        local("redis-cli -n {} FLUSHDB".format(REDIS_PRODUCTION_CACHE_DB))
    else:
        local("redis-cli -n {} FLUSHDB".format(REDIS_SANDBOX_CACHE_DB))


def contributors():
    """Print a list of contributors through git."""
    with hide("running"):
        local("git --no-pager shortlog -ns")


def deploy():
    """Deploy to production."""
    _require_root()

    if not confirm("This will apply any available migrations to the database. Has the database been backed up?"):
        abort("Aborted.")
    if not confirm("Are you sure you want to deploy?"):
        abort("Aborted.")

    with lcd(PRODUCTION_DOCUMENT_ROOT):
        with shell_env(PRODUCTION="TRUE"):
            local("git pull")
            with open("requirements.txt", "r") as req_file:
                requirements = req_file.read().strip().split()
                try:
                    pkg_resources.require(requirements)
                except pkg_resources.DistributionNotFound:
                    local("pip install -r requirements.txt")
                except Exception:
                    traceback.format_exc()
                    local("pip install -r requirements.txt")
                else:
                    puts("Python requirements already satisfied.")
            with prefix("source /usr/local/virtualenvs/ion/bin/activate"):
                local("./manage.py collectstatic --noinput", shell="/bin/bash")
                local("./manage.py migrate", shell="/bin/bash")
            restart_production_gunicorn(skip=True)

    puts("Deploy complete.")


def forcemigrate(app=None):
    """Force migrations to apply for a given app."""
    if app is None:
        abort("No app name given.")
    local("./manage.py migrate {} --fake".format(app))
    local("./manage.py migrate {}".format(app))


def inspect_decorators():
    """Inspect decorators in views."""
    local("grep -r 'def .*(request' intranet/apps/ -B1 | less")


def generate_docs():
    """Build Sphinx documentation."""
    local("sphinx-build -W -b html docs -d build/sphinx/doctrees build/sphinx/html")

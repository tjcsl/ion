# Working on Ion

Ion is TJHSST's Django intranet. Start with the app owning the behavior, trace its URL, view, permission checks, and model, then read its existing tests. Keep changes focused and preserve unrelated work in the checkout.

## Start here

- `dev` is the development integration branch and PR target; `master` is production. Do not assume a `main` branch exists. Inspect `git status --short --branch` and `git remote -v` before changing branches or publishing.
- The application requires Python 3.13+. Dependencies are in `requirements.txt` and `requirements-dev.txt`; Docker installs them and the system libraries.
- Run `python3 scripts/dev.py doctor` from the repository root to diagnose the local Docker environment. It checks Docker, running services, the mounted checkout, and the presence of local settings without starting services or changing files.
- Setup: [development environment](docs/source/setup/setup.md). Tests: [testing guide](docs/source/developing/testing.rst). Contribution rules: [contributing](docs/source/developing/contributing.md).

## Find the code

| Area | Start with |
| --- | --- |
| Routes and settings | `intranet/urls.py`, `intranet/settings/__init__.py`, app `urls.py` |
| Login and access control | `intranet/apps/auth/`, especially `decorators.py` and `rest_permissions.py` |
| Users and group permissions | `intranet/apps/users/models.py`, `intranet/apps/groups/` |
| Eighth period scheduling and attendance | `intranet/apps/eighth/models.py`, `views/`, `tests/` |
| Page markup and styling | `intranet/templates/<app>/`, `intranet/static/css/`, `intranet/static/js/` |
| Commands and imports | App `management/commands/`; data imports in `intranet/apps/dataimport/` |
| Shared test helpers | `intranet/test/ion_test.py`; eighth helpers in `intranet/apps/eighth/tests/eighth_test.py` |
| CI source | `ci/spec.yml`; regenerate `.github/workflows/ci.yml` with `python3 ci/regen-workflow.py` |
| API reference generation | `scripts/build_docs.py`, `docs/source/reference_index/` |

Eighth period separates reusable activities (`EighthActivity`), dated blocks (`EighthBlock`), an activity scheduled in a block (`EighthScheduledActivity`), and a user's signup (`EighthSignup`). Check which layer owns a rule before changing scheduling behavior.

## Implement and verify

Run these commands from the repository root:

```sh
# Target the affected app, class, or test method first.
python3 scripts/dev.py test intranet.apps.polls
python3 scripts/dev.py test intranet.apps.auth.tests.LoginViewTest -v 2

# Full application suite when the scope calls for it.
python3 scripts/dev.py test

# Development helper tests require only the Python standard library.
python3 -m unittest discover -s scripts -p test_dev.py -v

# Required before committing; uses the repository's pinned hooks.
pre-commit run --all-files
```

- Use Django's test runner. Most apps use `tests.py`; eighth uses a `tests/` package, and standalone `test_*.py` modules are also discovered. `IonTestCase` supplies login and admin helpers; `SimpleTestCase` suits code that does not query the database.
- Tests switch the default database to in-memory SQLite and disable migrations in `intranet/settings/__init__.py`. Docker's local settings can still point caches and other integrations at Redis. A passing unit suite does not verify PostgreSQL migrations.
- For model changes, include migrations and check them in the local development environment: `docker compose -f config/docker/docker-compose.yml exec -T django python manage.py makemigrations --check --dry-run`. Test migration behavior separately when relevant.
- Use relative imports within the application, four-space indentation, and the Ruff rules in `pyproject.toml` (150-character lines). Add regression tests for changed behavior, including permission failures when access rules change.
- When adding or removing application Python modules, run `python3 scripts/build_docs.py` and review the generated reference-index diff. Build published docs with the dependencies in `docs/requirements.txt` and `make -C docs html`.
- Follow Conventional Commits: lowercase description, at most 72 characters per line, blank line before the body. Keep generated CI files synchronized with their source.
- Report what changed, the checks actually run, and checks blocked by the environment. Do not describe mocked command tests as a successful Docker or application test run.

## Local environment details

Compose lives in `config/docker/docker-compose.yml`; its services are `django`, `postgres`, `redis`, `celery`, and `celerybeat`. The app is served at `http://localhost:8080`. Container names and the `ion-pgdata` volume are shared across checkouts; separate Git worktrees do not create isolated Docker environments.

First startup runs `config/docker/initial_setup.sh` through `entrypoint.sh`, writes `config/docker/first-run.log`, copies development settings, migrates, and creates sample data. The log is created before setup finishes, so its existence alone does not prove setup succeeded. Inspect logs before rerunning setup; it creates more sample data.

Keep local credentials and student data out of commits and logs. Do not replace an existing `intranet/settings/secret.py` as a routine troubleshooting step. Public security reporting guidance is in [the security policy](docs/source/security.md).

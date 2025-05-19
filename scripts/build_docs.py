#!/bin/env python3

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

ION_ROOT = Path(__file__).parent.parent

INTRANET = ION_ROOT / "intranet"
APPS = INTRANET / "apps"
MIDDLEWARE = INTRANET / "middleware"

DOCS = ION_ROOT / "docs" / "source"
REF_INDEX = DOCS / "reference_index"
APPS_REF_INDEX = REF_INDEX / "apps"
MIDDLEWARE_REF = REF_INDEX / "middleware.rst"

INDENT = "   "

IGNORE = (
    "__init__.py",
    "__pycache__",
    "migrations",
)


def base_format(name: str, mod: str, toctree: str) -> str:
    h1 = "#" * len(name)
    return f"""
{h1}
{name}
{h1}

.. currentmodule:: {mod}

.. autosummary::
{INDENT}:toctree: {toctree}

""".lstrip()


def get_base_format_apps(name: str):
    return base_format(name, f"intranet.apps.{name}", "../../reference")

def get_base_format_middleware(name: str):
    return base_format(name, "intranet.middleware", "../reference")

def recursively_get_appfiles(path: Path) -> Iterable[Path]:
    for app in sorted(path.iterdir()):
        if app.is_dir() and app.name not in IGNORE:
            yield from recursively_get_appfiles(app)
        yield app

def write_apps():
    for path in APPS.iterdir():
        appname = path.name
        if appname in IGNORE or not path.is_dir():
            continue
        s = get_base_format_apps(appname)
        changed = False
        for file in recursively_get_appfiles(path):
            if file.name in IGNORE or file.suffix != ".py":
                continue
            formatted = str(file.relative_to(path).with_suffix('')).replace('/', '.')
            s += f"{INDENT}{formatted}\n"
            changed = True

        # don't write empty stuff
        if not changed:
            continue

        path = APPS_REF_INDEX / f"{appname}.rst"
        path.write_text(s)

        print(f'{path.with_suffix("").name}/')

def write_middleware():
    s = get_base_format_middleware("Middleware")
    for path in sorted(MIDDLEWARE.iterdir()):
        appname = path.name
        if appname in IGNORE or path.suffix != ".py":
            continue
        s += f"{INDENT}~{path.relative_to(MIDDLEWARE).with_suffix('')}\n"

        print(appname)

    MIDDLEWARE_REF.write_text(s)


if __name__ == "__main__":
    APPS_REF_INDEX.mkdir(parents=True, exist_ok=True)

    print(f"{'APPS':^20s}")
    print(f"{''.ljust(20, '=')}\n")
    write_apps()

    print(f"\n{'Middleware':^20s}")
    print(f"{''.ljust(20, '=')}\n")
    write_middleware()

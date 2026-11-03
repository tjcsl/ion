#!/usr/bin/env python3
"""Diagnose the local Docker environment and run Ion tests from any directory."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ["docker", "compose", "-f", str(ROOT / "config/docker/docker-compose.yml")]
START_COMMAND = "docker compose -f config/docker/docker-compose.yml up --build -d"


class SetupError(Exception):
    """A local prerequisite is missing or unavailable."""


def probe(command, remedy):
    """Run a bounded diagnostic without displaying container configuration."""
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SetupError(remedy) from exc
    if result.returncode:
        raise SetupError(remedy)
    return result.stdout.strip()


def doctor():
    """Check prerequisites without starting services or changing local files."""
    if shutil.which("docker") is None:
        raise SetupError("Docker was not found. Install Docker with the Compose plugin, then start Docker.")
    probe(COMPOSE + ["version"], "Docker Compose is unavailable. Install the Docker Compose plugin.")
    probe(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        "Docker is not reachable. Start Docker Desktop or your Docker daemon and check your Docker context.",
    )
    print("OK: Docker and Compose are available.")

    services = set(
        probe(COMPOSE + ["ps", "--status", "running", "--services"], "Cannot inspect Ion services. Check Docker Compose configuration.").splitlines()
    )
    missing = {"django", "postgres", "redis"} - services
    if missing:
        raise SetupError(f"Services are not running: {', '.join(sorted(missing))}. From the repository root, run: {START_COMMAND}")

    container = probe(COMPOSE + ["ps", "--status", "running", "-q", "django"], "Cannot find the Django container.")
    raw_mounts = probe(["docker", "inspect", "--format", "{{json .Mounts}}", container], "Cannot inspect the Django container's checkout.")
    try:
        mounts = json.loads(raw_mounts)
        matches = any(mount.get("Destination") == "/ion" and Path(mount.get("Source", "")).resolve() == ROOT for mount in mounts)
    except (ValueError, TypeError, AttributeError) as exc:
        raise SetupError("Cannot determine which checkout is mounted in the Django container.") from exc
    if not matches:
        raise SetupError(
            "The Django container is not mounted from this checkout. Use the checkout that started it, or stop that stack and start this one. "
            "Ion's Compose configuration shares container names and a database volume across checkouts."
        )
    print("OK: Django, PostgreSQL, and Redis are running; Django uses this checkout.")

    if not (ROOT / "intranet/settings/secret.py").is_file():
        raise SetupError(
            "Local settings are missing. Inspect setup output with: docker compose -f config/docker/docker-compose.yml logs django. "
            "See docs/source/setup/setup.md for first-run troubleshooting."
        )
    print("OK: Local settings exist. Service health and application tests have not been checked.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "test"))
    parser.add_argument("test_args", nargs=argparse.REMAINDER, help="Django test labels and options, e.g. intranet.apps.polls -v 2")
    args = parser.parse_args(argv)
    if args.command == "doctor" and args.test_args:
        parser.error("doctor does not accept test arguments")
    try:
        doctor()
        if args.command == "doctor":
            return 0
        command = COMPOSE + ["exec", "-T", "django", "python", "./manage.py", "test", "--noinput"] + args.test_args
        print("Running Django tests in the local development container...", flush=True)
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    except SetupError as exc:
        print(f"Setup needed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Could not start tests: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)

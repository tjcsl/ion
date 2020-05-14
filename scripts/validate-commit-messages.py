#!/usr/bin/env python3
import re
import subprocess
import sys

"""
This script attempts to verify that certain
basic commit message conventions are followed.
"""


def get_output(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout.decode()


def join_nicely(items):
    items = list(map(str, items))
    if len(items) > 2:
        return ", ".join(items[:-1]) + ", and " + items[-1]
    else:
        return " and ".join(items)


def pluralize(value, singular="", plural="s"):
    return singular if value == 1 else plural


commits = []
for arg in filter(bool, map(str.strip, sys.argv[1:])):
    if ".." in arg:
        commits.extend(get_output(["git", "log", "--format=%H", arg]).split())
    else:
        commits.append(arg)

if not commits:
    sys.exit(0)


failed = False

for commit in commits:
    short_hash = get_output(["git", "show", "--format=format:%h", "--no-patch", commit])

    msg = get_output(["git", "show", "--format=format:%B", "--no-patch", commit])
    lines = msg.splitlines()

    errors = []

    if re.search(r"^(build|chore|ci|docs|feat|fix|perf|refactor|style|test)(\([a-z]+\))?: .*$", lines[0],) is None:
        errors.append("First line does not match format")

    if re.search(r"[^:]: [a-z].*$", lines[0]) is None:
        errors.append("First letter in commit message description is not lowercase.")

    if len(lines) > 1 and lines[1]:
        errors.append(
            "Second line must be empty. Please put a blank line between the subject (first line) and the body/extended description (third line "
            "onward). See the official git commit man page for more information: https://git-scm.com/docs/git-commit#_discussion"
        )

    long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 72]
    if long_lines:
        errors.append(
            "Line{} {} {} too long. Please limit all lines to 72 characters.".format(
                pluralize(len(long_lines)), join_nicely(long_lines), pluralize(len(long_lines), "is", "are"),
            )
        )

    if errors:
        print("The format of commit {} is invalid:".format(short_hash), file=sys.stderr)
        for error in errors:
            print("* {}".format(error), file=sys.stderr)

        failed = True


if failed:
    sys.exit(1)
else:
    print(
        "This commit message matches the correct format; *please review it for its content*.", file=sys.stderr,
    )

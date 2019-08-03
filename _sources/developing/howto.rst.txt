***************************
How to do Ion development
***************************

Formatting your code
====================

You can run ``./scripts/format.sh`` to automatically format your Python code to adhere to PEP8 standards.

Updating the dev branch
=======================

- git fetch --all
- git checkout dev
- git pull origin dev (note that if dev has been rebased, this may cause a conflict)
- if dev has been rebased, make *absolutely* sure that you don't have any local changes
  and run git reset --hard origin/dev this *will* destroy any local changes you have made to dev.
- git push

Fixing build
============

You can run ``./deploy`` to fix or find most of your build problems. If you add a new file, you may need to run ``./setup.py egg_info``.

Viewing documentation locally
=============================

You can view the documentation locally by running the commands below in the virtual machine.

- ./scripts/build_docs.sh
- cd build/sphinx/html
- python -m http.server 8080

Formatting commit messages
==========================

Effective June 2019, the Ion team uses the `Conventional Commit specification <https://www.conventionalcommits.org/en/v1.0.0-beta.4/#specification>`_ to format commit messages.

This means that all commit messages should be structured as follows
.. code-block:: text
    <type>[optional scope]: <description>

    [optional body]

    [optional footer]

The types that we use are:

- ``build``: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
- ``chore``: Changes that are grunt tasks etc; no production code change
- ``ci``: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
- ``docs``: Documentation only changes
- ``feat``: A new feature/enhancement
- ``fix``: A bug fix
- ``perf``: A code change that improves performance
- ``refactor``: A code change that neither fixes a bug nor adds a feature
- ``style``: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- ``test``: Adding missing tests or correcting existing tests

For example, if a commit adds a new feature to the ``emailfwd`` app, a good commit message would be:
.. code-block:: text
    feat(emailfwd): add email confirmation functionality

    Fixes #1

******************
Coding Style Guide
******************

Follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ (the official style guide for Python). Most PEP8 formatting conventions are enforced in the build by ``pylint``, ``flake8``, and a combination of ``black``, ``autopep8``, and ``isort``. Therefore, if you do not follow them, the build may not pass.

However, for Ion, we limit the lengths of lines to 150 characters, not 80 characters.

Note: CSS/JS/template formatting is enforced by ``scripts/static_templates_format.sh``. Currently, this just strips trailing whitespace.

Main points
===========

- Indent using 4 spaces.
- Use underscores in favor of camel case for all names except the names of classes.
- Limit the line length of docstrings or comments to 72 characters.
- Separate top-level functions and class definitions with two blank lines.
- Separate method definitions inside a class with a single blank line.
- Use two spaces before inline comments and one space between the pound sign and comment.
- Use a plugin for your text editor to check for/remind you of PEP8 conventions.
- When in doubt, running ``./scripts/format.sh`` will fix a lot of things.
- Capitalize and punctuate comments and Git commit messages properly.

What is enforced in the build
=============================

At the time of this writing, the GitHub Actions build runs the following commands:

.. code-block:: sh

        flake8 --max-line-length 150 --exclude=*/migrations/* .
        pylint --jobs=0 --disable=fixme,broad-except,global-statement,attribute-defined-outside-init intranet/
        isort --check --recursive intranet
        ./scripts.format.sh
        ./scripts/static_templates_format.sh  # Static/template files

Note: When the ``./scripts/format.sh`` and ``./scripts/static_templates_format.sh`` checks are run, the build will fail if they have to make any changes.

``flake8`` is a PEP8 style checker, ``pylint`` is a linter (but it also enforces some PEP8 conventions), and ``isort``, when called with these options, checks that all imports are sorted alphabetically.

``./scripts/format.sh`` runs ``black intranet && autopep8 --in-place --recursive intranet && isort --recursive intranet``. The reason for the multiple commands is that ``black`` introduces certain formatting changes which ``flake8``/``pylint`` do not agree with (and offers no options to change them), so we have ``autopep8`` fix it.

It is recommended that you run all of these locally before opening a pull request (though the Ion developers sometimes skip running the ``pylint`` check locally because it takes a long time to run). All of them are intended to be run from the root directory of the Git repository.

If ``flake8`` or ``pylint`` throw errors, the error messages are usually human-readable. if ``isort`` gives any errors, you can have it automatically correct the order of all imports by running ``isort --recursive intranet``. If the build fails because running ``scripts/format.sh`` resulted in changes, you can simply run  ``./scripts/format.sh`` to fix your formatting.

Imports
=======

- Group imports in the following order:
    #. Standard library imports
    #. Third-party imports
    #. Imports from Django
    #. Local imports

- Within these groups, place ``from ... import ...`` imports after ``import ...`` imports, and order imports alphabetically within *those* groups.

- Avoid using ``from ... import *``.

- Explicitly import each module used.

- Use relative imports to avoid hardcoding a module's package name. This greatly improves portability and is useful when importing from another module in the current app.

Examples
--------

Standard library imports:

.. code-block:: python

        from math import sqrt
        from os.path import abspath

Core Django imports:

.. code-block:: python

        from django.db import models

Third-party app imports:

.. code-block:: python

        from django_extensions.db.models import TimeStampedModel

Good:

.. code-block:: python

        from .models import SomeModel  # explicit relative import
        from otherdjangoapp.models import OtherModel  # absolute import

Bad:

.. code-block:: python

        # intranet/apps/users/views.py
        from intranet.apps.users.models import MyModel  # absolute import within same package


References
==========

- `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_.
- `Google HTML/CSS Style Guide <https://google.github.io/styleguide/htmlcssguide.html>`_.
- `Google Javascript Style Guide <https://google.github.io/styleguide/jsguide.html>`_.
- `PEP8: Official Python Style Guide <https://www.python.org/dev/peps/pep-0008/>`_.

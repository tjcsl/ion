******************
Coding Style Guide
******************

Follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ (the official style guide for Python).
However, if you want, you can use your own personal style guide, and then use ``pre-commit`` to format before committing.

.. caution::

  The CI will fail if the code is not formatted according to ``pre-commit``, so it's recommendded to use ``pre-commit``.

Main points
===========

- Indent using 4 spaces.
- Use underscores in favor of camel case for all names. For classes use PascalCase.
- Limit the line length of docstrings or comments to 72 characters.
- Separate top-level functions and class definitions with two blank lines.
- Separate method definitions inside a class with a single blank line.
- Use two spaces before inline comments and one space between the pound sign and comment.
- Use a plugin for your text editor to check for/remind you of PEP8 conventions.
- When in doubt, running ``pre-commit run --all-files`` will fix a lot of things.
- Capitalize and punctuate comments and Git commit messages properly.


.. _pre_commit:

What is enforced in the build
=============================

At the time of this writing, the GitHub Actions build runs the following commands:

.. code-block:: bash

    pre-commit run --all-files


It will fail if it has to make changes to the code.

The ``pre-commit`` config should run ``ruff``, ``codespell``, and some other linters. Most of the time it should autofix problems,
but there may be some linting errors that require manual intervention.

Imports
=======

- Avoid using ``from ... import *``.

- Explicitly import each module used.

- Use relative imports to avoid hardcoding a module's package name. This greatly improves portability and is useful when importing
  from another module in the current app.

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

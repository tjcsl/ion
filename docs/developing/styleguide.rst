******************
Coding Style Guide
******************

Follow `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ (the official style guide for Python).

However, for Ion, we limit the lengths of lines to 150 characters, not 80 characters.

Main points:

- Indent using 4 spaces.
- Use underscores in favor of camel case for all names except the names of classes.
- Limit the line length of docstrings or comments to 72 characters.
- Separate top-level functions and class definitions with two blank lines.
- Separate method definitions inside a class with a single blank line.
- Use two spaces before inline comment and one space between the pound sign and comment.
- Use a plugin for your text editor to check for/remind you of PEP8 conventions.
- Run the ``flake8`` linter periodically.
- Capitalize and punctuate comments and Git commit messages properly.

Imports
=======

- Group imports in the following order:
    #. Standard library imports
    #. Third-party imports
    #. Imports from Django
    #. Local imports

- Avoid using ``import *``

- Explicitly import each module used

- Use explicit relative imports to avoid hardcoding a module's package. This greatly improves portability and is useful when importing from another module in the current app.

- Do not use implicit relative imports.


Examples
--------

Standard library imports:

.. code-block:: python

        from math import sqrt
        from os.path import abspath

Core Django imports:

.. code-block:: python

        from django.db import models

Third-party app imports

.. code-block:: python

        from django_extensions.db.models import TimeStampedModel

Imports from your apps

.. code-block:: python

        from intranet.models import User

Good:

.. code-block:: python

    from .models import SomeModel  # explicit relative import
    from  otherdjangoapp.models import OtherModel  # absolute import

Bad:

.. code-block:: python

    from currentapp.models import MyModel  # implicit relative import


References
==========

- `Google Python Style Guide <https://google.github.io/styleguide/pyguide.html>`_.
- `Google HTML/CSS Style Guide <https://google.github.io/styleguide/htmlcssguide.html>`_.
- `Google Javascript Style Guide <https://google.github.io/styleguide/jsguide.html>`_.
- `PEP8: Official Python Style Guide <https://www.python.org/dev/peps/pep-0008/>`_.

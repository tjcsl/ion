******************
Coding Style Guide
******************

Follow `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ (the official style guide for Python).

Note that the `flake8` tool can be very useful in this regard.

Main points:

- Indent using 4 spaces.
- Use underscores in favor of camel case for all names except the naems of classes.
- Limit all lines to a maximum of 79 characters.
- Limit the line length of docstrings or comments to 72 characters.
- Separate top-level functions and class definitions with two blank lines.
- Separate method definitions inside a class with a single blank line.
- Use two spaces before inline comment and one space between the pound sign and comment/
- Use a plugin for your text editor to check for/remind you of PEP8 conventions.
- Capitalize and punctuate comments and git commit messages properly.

Imports
=======

- Group imports in the following order:
    #. Standard library imports
    #. Imports from core Django
    #. Related third-party imports
    #. Local application or library specific imports, imports from Django apps

- Avoid using ``import *``

- Explicitly import each module used


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



Explicit relative imports
    Used to avoid hardcoding a module's package. This greatly improves portability. Use these when importing from another module in the current app.

Absolute imports
    Used when importing outside the current app.

Implicit relative imports
    Don't use these. Using them makes it very difficult to change the name of the app, reducing portability.


Good:

.. code-block:: python

    from .models import SomeModel  # explicit relative import
    from  otherdjangoapp.models import OtherModel  # absolute import

Bad:

.. code-block:: python

    from currentapp.models import MyModel  # implicit relative import


References
==========

- `Google Python Style Guide <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_.
- `Google HTML/CSS Style Guide <http://google-styleguide.googlecode.com/svn/trunk/htmlcssguide.xml>`_.
- `Google Javascript Style Guide <http://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml>`_.
- `PEP8 Official Python Style Guide <http://www.python.org/dev/peps/pep-0008/>`_.

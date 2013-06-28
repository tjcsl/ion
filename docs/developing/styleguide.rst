******************
Coding Style Guide
******************

- Follow PEP8 (the official style guide for Python)
    - Main points:
        - Use 4 spaces per indentation level

Separate top-level functions and class definitions with two blank lines
Separate method definitions inside a class with a single blank line
Use two spaces before inline comment and one space between the pound sign and comment
Use a plugin for your text editor to check for/remind you of PEP8 conventions
Capitalize and punctuate comments and git commit messages properly
Group imports in the following order
Standard library imports
Imports from core Django
Related third-party imports
Local application or library specific imports, imports from Django apps
Example imports:
                  # Stdlib imports
        from math import sqrt
        from os.path import abspath

        # Core Django imports
        from django.db import models

        #Third-party app imports
        from django_extensions.db.models import TimeStampedModel

        # Imports from your apps
        from intranet.models import User
Use explicit relative imports to avoid hardcoding a module's package so modules aren't tied to the architecture around them
    Example:
    from .models import RandomModel  # explicit relative import -- used when importing from another module in the current app
    from .forms import RandomForm
    from  otherdjangoapp.models import OtherModel  # absolute import -- use when importing from outside the current app

    Don't do this:
    from currentapp.models import MyModel  # implicit relative -- makes it hard to change name of app, etc.
- Avoid using import *
    Explicitly import each module used
Performance Guidelines
Index everything you want to query on and only query with indexes
"Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live."
--John Woods comp.lang.c++

"First, solve the problem. Then, write the code."
--John Johnson

“ Any fool can write code that a computer can understand. Good programmers write code that humans can understand. ”
--Martin Fowler

“Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it. ”
--Brian Kernighan



Reference
=========

- `Google Python Style Guide <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_.
- `Google HTML/CSS Style Guide <http://google-styleguide.googlecode.com/svn/trunk/htmlcssguide.xml>`_.
- `Google Javascript Style Guide <http://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml>`_.
***************************
How to perform common tasks
***************************

Formatting your code
====================

You can run ``autopep8 -ir --max-line-length=200`` to check your code for formatting errors.

You can run ``./scripts/format.sh`` to automatically format your Python code to adhere to PEP8 standards.

Viewing documentation locally
=============================

You can view the documentation locally by running the commands below in the virtual machine.

.. code-block:: bash

    $ ./scripts/build_docs.sh
    $ cd build/sphinx/html
    $ python -m http.server 8080

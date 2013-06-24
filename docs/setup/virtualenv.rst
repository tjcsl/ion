*********************
Setting up Virtualenv
*********************

SSH into Ion.

Navigate to ``/usr/local/virtualenvs``:

.. code-block:: bash

    $ cd /usr/local/virtualenvs

As root, create your Virtualenv, as follows. you should name it according to standard as ``<initials>-ion`` (e.g. ``aw-ion`` for Angela William):

.. code-block:: bash

    $ ksu
    $ virtualenv --distribute --no-site-packages <initials>-ion

Return to an unprivileged user:

.. code-block:: bash

    $ exit

Navigate to your home directory (``cd``), where you have a sandbox set up (if not, see Setting up Your Sandbox), and start working in your virtualenv:

.. code-block:: bash

    $ cd ~
    $ workon <initials>-ion

Install the requirements for a testing version of Intranet (change this to the staging area when one is set up):

.. code-block:: bash

    $ pip install -r /usr/local/www/intranet3/requirements/local.py

Make sure that you have the requirements listed in that file:

.. code-block:: bash

    $ pip freeze

To check if your install worked, make sure your environment has all the requisite packages.

.. code-block:: bash

    $ pip freeze > freeze.txt
    $ cat /usr/local/www/requirements.txt > req.txt
    $ diff -q pip.txt req.txt

If there’s no output, your sandbox should be ready to go. Finally, clean up some of your temporary files:

.. code-block:: bash

    $ rm freeze.txt req.txt
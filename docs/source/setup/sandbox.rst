***********************
Setting up Your Sandbox
***********************


**Sandboxes are deprecated.** Instead, :doc:`use Vagrant<vagrant>` to manage your development environment.

----------
Virtualenv
----------

SSH into Ion. You will need a CSL principal and to be added to the ion group.

Navigate to ``/usr/local/virtualenvs``:

.. code-block:: bash

    $ cd /usr/local/virtualenvs

As root, create your Virtualenv with a name following the format ``<initials>-ion`` (e.g. ``aw-ion`` for Angela William):

.. code-block:: bash

    $ ksu
    $ virtualenv --distribute --no-site-packages <initials>-ion

Return to an unprivileged user, navigate to your home directory, and activate your virtualenv.

.. code-block:: bash

    $ exit
    $ cd ~
    $ workon <initials>-ion

--------
Codebase
--------

While still in your home directory, clone the Git repository.

.. code-block:: bash

    $ git clone https://github.com/<Github username>/ion.git

Checkout a local copy of the ``dev`` branch.

.. code-block:: bash

    $ git checkout -b dev origin/dev

Install the requirements for a testing version of Intranet.

.. code-block:: bash

    $ pip install -r requirements/local.txt

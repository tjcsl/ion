*********************
Setting up the Server
*********************

-----------------
Portage USE flags
-----------------

Add the following flags to ``/etc/portage/package.use``::

    net-nds/openldap kerberos sasl
    dev-python/python-ldap sasl
    dev-libs/cyrus-sasl kerberos ldap


------------------
LDAP Configuration
------------------

In order to have LDAP work properly, you have to have the following schema included:
* core
* cosine (if you have sound support)
* nis
* inetorgperson
* dyngroup
* iodine
If you fail to have one of these imported, slapd will segfault without any error messages.
You then need to add a line to include intranet's slapd.acl. This also has a possibility of bringing
about silent segfaults; it is recommended to do this one step at a time.

----------
PostgreSQL
----------

First, install the PostgreSQL server.

.. code-block:: bash

    $ emerge dev-db/postgresql

The following command will print out the command you should run to configure postgres.

.. code-block:: bash

    $ grep "config =dev-db/postgres" /var/log/portage/elog/summary.log

Run the printed command. Then start the PostgreSQL server.

.. code-block:: bash

    $ /etc/init.d/postgresql-9.4 start

Add the Postgres service to the default runlevel.


.. code-block:: bash

    $ rc-update add postgresql-9.4 default

Become root, then run the following command to add an admin user to the postgres group. Replace <admin username> with the username of someone you would like to make a Postgres admin.

.. code-block:: bash

    $ usermod -aG postgres <admin username>

Become the user ``postgres``.

.. code-block:: bash

    $ su - postgres

Create the admin user in postgres

.. code-block:: bash

    $ createuser -s <admin username>

Exit from ``su``. Repeat the last three steps (since you became root) for all the users who should have admin Postgres access. Then exit from ``ksu``.

Create the production Ion database.

.. code-block:: bash

    $ createdb -h localhost ion
    $ createdb -h localhost ion-dev

-----
Redis
-----

Install Redis.

.. code-block:: bash

    $ emerge redis

Start Redis.

.. code-block:: bash

    $ /etc/init.d/redis start

Add the Redis service to the default runlevel.

.. code-block:: bash

    $ rc-update add redis default

------
Python
------

Install the ``python-ldap`` module, the Cyrus-SASL C library, and the Pip package manager.

.. code-block:: bash

    $ emerge net-nds/openldap
    $ emerge dev-libs/cyrus-sasl
    $ emerge python-ldap
    $ emerge dev-python/pip
    $ emerge dev-python/fabric

----------
Virtualenv
----------

Create a directory for virualenvs.

.. code-block:: bash

    $ mkdir /etc/local/virtualenvs

Install virtualenv and virtualenvwrapper.

.. code-block:: bash

    $ pip install virtualenv virtualenvwrapper

Append the following to ``/etc/bash/bashrc``.

.. code-block:: bash

    # Virtualenv/Pip config
    export VIRTUALENV_DISTRIBUTE=true
    export PIP_VIRTUALENV_BASE=/usr/local/virtualenvs
    export WORKON_HOME=/usr/local/virtualenvs
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python
    export PIP_DOWNLOAD_CACHE=/usr/local/virtualenvs/cache
    source /usr/bin/virtualenvwrapper.sh

Reload the bashrc.

.. code-block:: bash

    $ source /etc/bash/bashrc

Make a production virtualenv.

.. code-block:: bash

    mkvirtualenv ion

Confirm that your prompt now appears something like this:

.. code-block:: bash

    (ion)awilliam@ion ~ $

---
Git
---

Install Git.

.. code-block:: bash

    $ emerge dev-vcs/git

-------------------------------
Set up the production code base
-------------------------------

Exit from root. Create the local shared Git repository.

.. code-block:: bash

    $ cd /shared/git

Set up SSH access to Github by following `this tutorial <https://help.github.com/articles/generating-ssh-keys>`_. Then clone the Ion Git repository and give all users in the "ion" group access.

.. code-block:: bash

    $ git clone --bare git@github.com:tjcsl/ion.git
    $ cd ion.git
    $ git config core.sharedRepository true
    $ chgrp -R ion .

Rename the main branch to "upstream" (``git remote rename`` doesn't seem to work in this situation).

.. code-block:: bash

    $ git remote add upstream git@github.com:tjcsl/ion.git
    $ git fetch upstream
    $ git remote rm origin

Add the Git hook to automatically push changes to Github by creating a post-receive hook (``touch hooks/post-receive``) and appending the following to that file:

.. code-block:: bash

    #!/bin/bash

    git push --all --tags github

Make the post-receive hook executable.

.. code-block:: bash

    $ chmod +x hooks/post-receive

Create a directory for the production code.

.. code-block:: bash

    $ ksu
    $ mkdir /var/www
    $ cd /var/www

Clone the shared repository.

.. code-block:: bash

    $ git clone /shared/git/ion.git

Ensure that your prompt still starts with ``(ion)``. If it doesn't, run the following.

.. code-block:: bash

    $ workon ion

Install all of the dependencies.

.. code-block:: bash

    $ pip install -U -r ion/requirements/production.txt

Initialize the ldap db.
.. code-block:: bash

    ldapadd -Q -c -f intranet/static/ldap/base.ldif

-----
Nginx
-----

Install Nginx.

.. code-block:: bash

    $ emerge www-servers/nginx

Replace ``/etc/nginx/nginx.conf`` with the config file in the Ion git repository.

.. code-block:: bash

    $ ksu
    $ mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    $ cp /var/www/ion/extras/nginx/nginx.conf /etc/nginx/nginx.conf

Start Nginx.

.. code-block:: bash

    $ /etc/init.d/nginx start

Add the Nginx service to the default runlevel.

.. code-block:: bash

    $ rc-update add nginx default

----------
Supervisor
----------

Deactivate the virtualenv if your prompt still starts with (ion).

.. code-block:: bash

    $ deactivate

Install Supervisor.

.. code-block:: bash

    $ pip install supervisor

Add the Supervisor config file from the Ion repository.

.. code-block:: bash

    $ ksu
    $ cp /var/www/ion/extras/supervisord.conf /etc/supervisord.conf

Add the init.d script from the Ion repository. (Based on the script from `here <https://github.com/Supervisor/initscripts/blob/master/gentoo-matagus>`_)

.. code-block:: bash

    $ cp /var/www/ion/extras/supervisord /etc/init.d/
    $ chmod +x /etc/init.d/supervisord

Start Supervisor.

.. code-block:: bash

    $ /etc/init.d/supervisord start

Add the Supervisor service to the default runlevel.

.. code-block:: bash

    $ rc-update add supervisord default

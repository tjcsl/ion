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

----------
PostgreSQL
----------

First, install the PostgreSQL server.

.. code-block:: bash

    $ emerge dev-db/postgresql-server

The following command will print out the command you should run to configure postgres.

.. code-block:: bash

    $ grep "config =dev-db/postgres" /var/log/portage/elog/summary.log

Run the printed command. Then start the PostgreSQL server.

.. code-block:: bash

    $ /etc/init.d/postgresql-9.2 start

Add the Postgres service to the default runlevel.


.. code-block:: bash

    $ rc-update add postgresql-9.2 default

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

Set up SSH access to Bitbucket by following `this tutorial <https://confluence.atlassian.com/display/BITBUCKET/Set+up+SSH+for+Git>`_. Then clone the Ion Git repository and give all users in the "ion" group access.

.. code-block:: bash

    $ git clone --bare git@bitbucket.org:tjhsstintranet/intranet3.git
    $ cd intranet3.git
    $ git config core.sharedRepository true
    $ chgrp -R ion .

Rename the main branch to "bitbucket" (``git remote rename`` doesn't seem to work in this situation).

.. code-block:: bash

    $ git remote add bitbucket git@bitbucket.org:tjhsstintranet/intranet3.git
    $ git fetch bitbucket
    $ git remote rm origin

Add the Git hook to automatically push changes to Bitbucket by creating a post-receive hook (``touch hooks/post-receive``) and appending the following to that file:

.. code-block:: bash

    #!/bin/bash

    git push --all bitbucket
    git push --tags bitbucket

Make the post-receive hook executable.

.. code-block:: bash

    $ chmod +x hooks/post-receive

Create a directory for the production code.

.. code-block:: bash

    $ ksu
    $ mkdir /usr/local/www
    $ cd /usr/local/www

Clone the shared repository.

.. code-block:: bash

    $ git clone /shared/git/intranet3.git

Ensure that your prompt still starts with ``(ion)``. If it doesn't, run the following.

.. code-block:: bash

    $ workon ion

Install all of the dependencies.

.. code-block:: bash

    $ pip install -r intranet3/requirements/production.txt

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
    $ cp /usr/local/www/intranet3/extras/nginx/nginx.conf /etc/nginx/nginx.conf

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
    $ cp /usr/local/www/intranet3/extras/supervisord.conf /etc/supervisord.conf

Add the init.d script from the Ion repository. (Based on the script from `here <https://github.com/Supervisor/initscripts/blob/master/gentoo-matagus>`_)

.. code-block:: bash

    $ cp /usr/local/www/intranet3/extras/supervisord /etc/init.d/
    $ chmod +x /etc/init.d/supervisord

Start Supervisor.

.. code-block:: bash

    $ /etc/init.d/supervisord start

Add the Supervisor service to the default runlevel.

.. code-block:: bash

    $ rc-update add supervisord default

-------------
ElasticSearch
-------------

Install ElasticSearch. Portage may ask you to modify a few configuration files. Make the necessary changes and try again.

.. code-block:: bash

    $ emerge app-misc/elasticsearch

Start ElasticSearch.

.. code-block:: bash

    $ /etc/init.d/elasticsearch start

Add the ElasticSearch service to the default runlevel.

.. code-block:: bash

    $ rc-update add supervisord default




******************
Post-Install Steps
******************


After successfully :doc:`setting up the Vagrant environment<vagrant>`, you will want to actually access your sandbox.

Start by connecting to the Vagrant box using ``vagrant ssh``. (Consider running all of the following in a ``screen`` or ``tmux`` session.) Make sure you're in the ``intranet`` directory, and run ``python manage.py migrate``. This will set up the Postgres database.

You can then start the built-in Django web server with ``fab runserver``. Now that you are running the development server, open a browser to http://127.0.0.1:8080 and log in. If it fails, check the output of ``manage.py runserver``.

Setting Up Groups
=================

Currently, there are no default groups set up when you first install Ion. In order to grant yourself administrative privileges, you must be a member of the ``admin_all`` group.

To create and add yourself to the global administrator group, run the following commands:

.. code-block:: bash

    $ ./manage.py shell_plus
    Python 2.7.6 (default, Mar 22 2014, 22:59:56)
    (InteractiveConsole)
    >>> user = User.get_user(username="YOURUSERNAME")
    >>> group = Group.objects.get_or_create(name="admin_all")[0]
    >>> user.groups.add(group)
    >>> user.is_superuser = True
    >>> user.save()


Populating the Search Index
===========================

Run the following command to populate the Elasticsearch index with users.

.. code-block:: bash

    $ ./manage.py update_index

Connecting and Disconnecting from the VM
========================================

When you want to close the VM environment, make sure you have exited out of the ssh session and then run ``vagrant suspend``. To resume the session, run ``vagrant resume``. Suspending and resuming is significantly faster than halting and starting, and also dumps the contents of the machine's RAM to disk.

Updating Block Dates
====================

Currently, the fixtures containing test data include Iodine data from the 2014-2015 school year. If you would like to modify this data so that all of the eighth period blocks occur in the future, run the following:

.. code-block:: bash

    $ ./manage.py shell_plus
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    (InteractiveConsole)
    >>> from dateutil.relativedelta import relativedelta
    >>> for blk in blks:
    ...     blk.date += relativedelta(months=+6)
    ...     blk.save()

Increasing RAM
==============

With the default RAM size of 512MB, you may run into performance constraints. Additionally, ElasticSearch will not run with less than 1GB of RAM. It is highly recommended to bump the VM's amount of memory, through VirtualBox Manager, to at least 1.5GB.
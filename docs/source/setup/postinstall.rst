******************
Post-Install Steps
******************


After successfully :doc:`setting up the Vagrant environment<vagrant>`, you will want to actually access your sandbox.

Start by connecting to the Vagrant box using ``vagrant ssh``. Make sure you're in the ``intranet`` directory, and run ``python manage.py migrate``. This will set up the Postgres database.

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

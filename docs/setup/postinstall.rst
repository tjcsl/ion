******************
Post-Install Steps
******************


After successfully :doc:`setting up the Vagrant environment<vagrant>`, you will want to actually access your sandbox.

Start by connecting to the Vagrant box using ``vagrant ssh``. (Consider running all of the following in a ``screen`` or ``tmux`` session.)

After you connect to your Vagrant box, make sure you are in the ``intranet`` directory and run ``workon ion`` to access your Python virtual environment.

You will then need to run ``python manage.py migrate`` to set up the Postgres database.

You can then start the built-in Django web server with ``fab runserver``. Now that you are running the development server, open a browser to http://127.0.0.1:8080 and log in (the default master password is ``swordfish``). If it fails, check the output of ``python manage.py runserver``.

Setting Up Groups
=================

Currently, there are no default groups set up when you first install Ion. In order to grant yourself administrative privileges, you must be a member of the ``admin_all`` group.

To create and add yourself to this group, run the following commands (substituting your username for ``<USERNAME>``):

.. code-block:: bash

    $ ./manage.py shell_plus
    >>> user = User.objects.get_or_create(username="<USERNAME>")[0]
    >>> group = Group.objects.get_or_create(name="admin_all")[0]
    >>> user.groups.add(group)
    >>> user.is_superuser = True
    >>> user.save()


Connecting and Disconnecting from the VM
========================================

When you want to close the VM environment, make sure you have exited out of the ssh session and then run ``vagrant suspend``. To resume the session, run ``vagrant resume``. Suspending and resuming is significantly faster than halting and starting, and also dumps the contents of the machine's RAM to disk.

Setting up Files
================

You can find a list of file systems at ``intranet/apps/files/models.py``. To add these systems so that they appear on the Files page, run the statements found in the file. A sample is shown below:

.. code-block:: bash

    $ ./manage.py shell_plus
    >>> Host.objects.create(name="Computer Systems Lab", code="csl", address="remote.tjhsst.edu", linux=True)

Increasing RAM
==============

With the default RAM size of 1024MB, you may run into performance constraints.
If you encounter signifigant issues, it is recommended to bump the VM's amount of memory, through VirtualBox Manager, to at least 2GB.

:doc:`Continue with these steps on installing fixtures.<fixtures>`

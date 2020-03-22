******************
Setting up Vagrant
******************

**The following commands should be executed in your host machine's console.**

Vagrant is used to manage Ion's development environment so that it closely resembles the production environment. To get started, download and install Virtualbox from `here <https://www.virtualbox.org/wiki/Downloads>`__ and Vagrant from `here <http://docs.vagrantup.com/v2/installation/index.html>`__.

Ensure you have an SSH key set up with GitHub by running ``ssh -T git@github.com``. You should be greeted by your username. If not, set up an SSH key with GitHub by following `these instructions <https://help.github.com/articles/generating-an-ssh-key/>`_.

With Vagrant and Virtualbox installed, clone the Ion repository onto the host computer and ``cd`` into the new directory.

Note: if your host machine is running Windows, please run ``git config core.autocrlf input`` before cloning to prevent line ending issues.

.. code-block:: bash

    $ git clone git@github.com:tjcsl/ion.git intranet
    $ cd intranet

In the ``config`` directory, copy the file ``devconfig.json.sample`` to ``devconfig.json`` and edit the properties in ``devconfig.json`` as appropriate. Ensure ``ssh_key`` is set to the same SSH key registered with GitHub (e.g. ``id_rsa``).

Run ``vagrant plugin install vagrant-vbguest``
If you are on Windows, also run ``vagrant plugin install vagrant-winnfsd``

Run ``vagrant up && vagrant reload`` and wait while the development environment is set up. 

If you are asked to select a network interface for bridging, enter the number corresponding to one that is active. To automatically select this interface in the future, set the "network_interface" key in ``devconfig.json`` to the name of the interface you selected (e.g. ``"en0: Wi-Fi (AirPort)"``). 

There may be repeated warnings similar to "``Remote connection disconnect`` and ``Warning: Connection aborted. Retrying...`` on the second ``vagrant up``. After several minutes they will stop. Once the provisioning process is complete, run ``vagrant ssh`` to log in to the development box.

**The following commands should be executed in your development box.**

Move into the ``intranet`` directory and run ``workon ion`` to load the Python dependencies. ``workon ion`` should always be the first thing you run after you SSH into the development box.

The Git repository on the host computer is synced with ``~/intranet`` on the virtual machine, so you can edit files within the repo on the host computer with a text editor of your choice and the changes will be immediately reflected on the virtual machine.

:doc:`Continue with these post-install steps.<postinstall>`

Troubleshooting
===============

If you get a ``SIOCADDRT: Network is unreachable`` error when running ``vagrant up``, you need to start the OpenVPN client.

If you see a ``Adding routes to host computer...`` message, you probably forgot to start the OpenVPN client.

If you get a message that begins with ``Vagrant failed to initialize at a very early stage``, run the commands in this list in order until one of them succeeds and Vagrant works again:

#. ``vagrant plugin update`` (updates all plugins)
#. ``vagrant plugin repair`` (attempts to repair all plugins)
#. ``vagrant plugin expunge --reinstall`` (removes and re-installs all plugins)
#. If none of these work, see "If all else fails" below.

If all else fails
-----------------
If Vagrant errors every time you try to do anything and either 1) a solution is not listed here or 2) the solution does not work, then follow these steps:

#. Rename the ``.vagrant.d`` folder in your home directory to something else (which will effectively delete it from Vagrant's perspective)
#. Re-run the appropriate ``vagrant plugin install ...`` commands listed above.
#. When they finish, Vagrant should work again. You should then be able to safely delete the old ``.vagrant.d`` directory.

If *that* doesn't work, contact a senior Ion developer.

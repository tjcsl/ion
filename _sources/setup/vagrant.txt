******************
Setting up Vagrant
******************

Vagrant is used to manage Ion's development environment so that it closely resembles the production environment. To get started, download and install Virtualbox from `here <https://www.virtualbox.org/wiki/Downloads>`__ and Vagrant from `here <http://docs.vagrantup.com/v2/installation/index.html>`__.

Ensure you have an SSH key set up with GitHub by running ``ssh -T git@github.com``. You should be greeted by your username. If not, set up an SSH key with GitHub by following `these instructions <https://help.github.com/articles/generating-ssh-keys/>`_.

With Vagrant and Virtualbox installed, clone the Ion repository onto the host computer and ``cd`` into the new directory.

Note: if your host machine is running Windows, please run ``git config core.autocrlf input`` before cloning to prevent line ending issues.

.. code-block:: bash

    $ git clone git@github.com:tjcsl/ion.git intranet
    $ cd intranet

In the ``config`` directory, copy the file ``devconfig.json.sample`` to ``devconfig.json`` and edit the properties in ``devconfig.json`` as appropriate. Ensure ``ssh_key`` is set to the same SSH key registered with GitHub (e.g. ``id_rsa``). Obtain the proper value for ``ldap_simple_bind_password`` from another Intranet developer of from the ``ion.tjhsst.edu`` VM.

Run ``vagrant plugin install vagrant-vbguest``

Run ``vagrant up && vagrant reload`` and wait while the development environment is set up. When asked to select a network interface for bridging, enter the number corresponding to one that is active. To automatically select this interface in the future, set the "network_interface" key in ``devconfig.json`` to the name of the interface you selected (e.g. ``"en0: Wi-Fi (AirPort)"``). There may be repeated warnings similar to "``Remote connection disconnect`` on the second ``vagrant up``. After several minutes they will stop. Once the provisioning process is complete, run ``vagrant ssh`` to log in to the development box.

Move into the ``intranet`` directory and run ``workon ion`` to load the Python dependencies. ``workon ion`` should always be the first thing you run after you SSH into the development box.

The Git repository on the host computer is synced with ``~/intranet`` on the virtual machine, so you can edit files within the repo on the host computer with a text editor of your choice and the changes will be immediately reflected on the virtual machine.

If you would like to populate the database with test data, run ``fab load_fixtures`` in the ``~/intranet`` directory. This process may take a lot of RAM and can unexpectedly quit. If this happens, run ``./manage.py flush`` to flush the database, exit the SSH session, run ``vagrant halt``, increase the VM's allotted memory in VirtualBox, and run ``vagrant up`` again.

Troubleshooting
===============

If you get a ``SIOCADDRT: Network is unreachable`` error when running ``vagrant up``, you need to start the openvpn client.

:doc:`Continue with these post-install steps.<postinstall>`

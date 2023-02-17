# Create an Ion Development Environment

You have two options when setting up a development environment for Ion: Docker or Vagrant. Docker is probably going to work better, so try it first.

The Git repository on the host computer is synced with ``~/intranet`` on the virtual machine, so you can edit files within the repo on the host computer with a text editor of your choice and the changes will be immediately reflected on the virtual machine.

# Docker

## Prerequisites

- [Docker](https://www.docker.com) is the containerization framework that runs Ion's individual services. Installation is OS-specific and instructions can be found [here](https://www.docker.com/products/docker-desktop/). On Windows and Mac, install Docker Desktop.
- [GitHub](https://github.com) is the version control system used by the CSL. Make sure that you have an account and an SSH key tied to that account that will allow you to push and pull code. Ensure you have an SSH key set up with GitHub by running ``ssh -T git@github.com``. You should be greeted by your username. If not, set up an SSH key with GitHub by following [these instructions](https://help.github.com/articles/generating-an-ssh-key/).

## Set Up

1. Create your own fork of the [``tjcsl/ion`` repository](https://github.com/tjcsl/ion.git).
2. Clone the Ion repositiory from your Ion fork by running ``git clone git@github.com:<YOUR_GITHUB_USERNAME>/ion.git intranet``. Note: if your host machine is running Windows, please run ``git config core.autocrlf input`` before cloning to prevent line ending issues.
3. Inside the Ion repository, edit the ``config/docker/make_admin.py`` file, replacing "\<YOUR_USERNAME\>" with your Ion username.
4. Run ``cd config/docker``.
5. Run ``docker-compose up -d``.

## Docker Post Set-Up

Navigate to http://localhost:8080 in the web browser of your choice. You might have to wait up to 60 seconds the first time that you create the container. When presented with the login page, log in with your Ion username and the password "notfish" (without the quotes).

## Useful Commands

### Interacting with the application:

If you need to run a Django command like ``makemigrations``, ``collectstatic`` or ``shell_plus``, run ``docker exec -it intranet bash`` in your terminal. That wlll give you a shell into the application container. You can also use this to run scripts like ``build_sources.sh``. If you need to view the output from or restart ``runserver``, run ``docker attach application``.

### Attaching to logs

To view logs of a container, run `docker logs [CONTAINER NAME] -f`. For example, to view the logs of the web server, run `docker logs intranet -f`.

# Vagrant

## Prerequisites

- [Virtualbox](https://www.virtualbox.org/) is a virtualization service that allows the creation of virtual machines. Installation is OS-specific and instructions can be found [here](https://www.virtualbox.org/wiki/Downloads). 
- [Vagrant](https://www.vagrantup.com/) is a command line utility for managing and setting up virtual machines and environments. Installation is OS-specific and instructions can be found [here](https://developer.hashicorp.com/vagrant/downloads).
- [GitHub](https://github.com) is the version control system used by the CSL. Make sure that you have an account and an SSH key tied to that account that will allow you to push and pull code. Ensure you have an SSH key set up with GitHub by running ``ssh -T git@github.com``. You should be greeted by your username. If not, set up an SSH key with GitHub by following [these instructions](https://help.github.com/articles/generating-an-ssh-key/).

## Set Up

1. Create your own fork of the [``tjcsl/ion`` repository](https://github.com/tjcsl/ion.git).
2. Clone the Ion repositiory from your Ion fork by running ``git clone git@github.com:<YOUR_GITHUB_USERNAME>/ion.git intranet``. Note: if your host machine is running Windows, please run ``git config core.autocrlf input`` before cloning to prevent line ending issues.
3. In the ``config/vagrant`` directory, copy the file ``devconfig.json.sample`` to ``devconfig.json`` and edit the properties in ``devconfig.json`` as appropriate. Ensure ``ssh_key`` is set to the same SSH key registered with GitHub (e.g. ``id_rsa``).
4. Run ``vagrant plugin install vagrant-vbguest``. If you are on Windows, also run ``vagrant plugin install vagrant-winnfsd``.
5. Run ``vagrant up && vagrant reload`` and wait while the development environment is set up. If you are asked to select a network interface for bridging, enter the number corresponding to one that is active. To automatically select this interface in the future, set the "network_interface" key in ``devconfig.json`` to the name of the interface you selected (e.g. ``"en0: Wi-Fi (AirPort)"``). There may be repeated warnings similar to "``Remote connection disconnect`` and ``Warning: Connection aborted. Retrying...`` on the second ``vagrant up``. After several minutes they will stop.
6. Once the provisioning process is complete, run ``vagrant ssh`` to log in to the development box.
7. Move into the ``intranet`` directory and run ``workon ion`` to load the Python dependencies. ``workon ion`` should always be the first thing you run after you SSH into the development box.

## Troubleshooting

If you get a ``SIOCADDRT: Network is unreachable`` error when running ``vagrant up``, you need to start the OpenVPN client.

If you see a ``Adding routes to host computer...`` message, you probably forgot to start the OpenVPN client.

If you get a message that begins with ``Vagrant failed to initialize at a very early stage``, run the commands in this list in order until one of them succeeds and Vagrant works again:

#. ``vagrant plugin update`` (updates all plugins)
#. ``vagrant plugin repair`` (attempts to repair all plugins)
#. ``vagrant plugin expunge --reinstall`` (removes and re-installs all plugins)
#. If none of these work, see "If all else fails" below.

### If all else fails

If Vagrant errors every time you try to do anything and either 1) a solution is not listed here or 2) the solution does not work, then follow these steps:

#. Rename the ``.vagrant.d`` folder in your home directory to something else (which will effectively delete it from Vagrant's perspective)
#. Re-run the appropriate ``vagrant plugin install ...`` commands listed above.
#. When they finish, Vagrant should work again. You should then be able to safely delete the old ``.vagrant.d`` directory.

If *that* doesn't work, contact a senior Ion developer.

## Vagrant Post-Install Steps

After successfully setting up the Vagrant environment, you will want to actually access your sandbox.

Start by connecting to the Vagrant box using ``vagrant ssh``. (Consider running all of the following in a ``screen`` or ``tmux`` session.)

After you connect to your Vagrant box, make sure you are in the ``intranet`` directory and run ``workon ion`` to access your Python virtual environment.

You will then need to run ``python manage.py migrate`` to set up the Postgres database.

You can then start the built-in Django web server with ``fab runserver``. Now that you are running the development server, open a browser to http://127.0.0.1:8080 and log in. If this is your first time attempting this, see "Setting Up Groups", then use the default master password (``swordfish``) to login. If it fails, check the output of ``python manage.py runserver``.

### Connecting and Disconnecting from the VM

When you want to close the VM environment, make sure you have exited out of the ssh session and then run ``vagrant suspend``. To resume the session, run ``vagrant resume``. Suspending and resuming is significantly faster than halting and starting, and also dumps the contents of the machine's RAM to disk.

## Changing Master Password

The master password for vagrant development enviornment is ``swordfish``.

In non-Vagrant environments, you should set a master password different from the default. Ideally, this password should have many bits of entropy and should be randomly generated.

We use the secure Argon2 hashing algorithim to secure our master password. To set the master password, set ``MASTER_PASSWORD`` to the string output of the below script (after changing values as appropriate) in ``secret.py``. After changing this value, restart Ion.

Currently, Ion requires that you use Argon2id to create the hash. You also must prepend ``argon2`` to the hash before putting it into ``secret.py``.

    from argon2 import PasswordHasher, low_level

    # Change this password to the new master password.
    password = "CHANGE_ME"

    # These are the Django defaults. Change as needed.
    time_cost = 2
    memory_cost = 512
    parallelism = 2
    h=PasswordHasher(time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism, type=low_level.Type.ID)
    print(h.hash(password))

# General Post-Setup

## Auto-generated development data

The setup process will automatically generate data for you to use in Ion development. This data includes:

- Users (students, teachers, admins, counselors)
- Eighth period blocks
- Eighth period activities (all types)
- Events (sports))

## Setting up Users

A large number of users for use in development is automatically generated for you. You may use the auto-generated users `admin`, `student`, and `teacher` for quick access to each of those types of accounts. To create other users, use the `create-users.py` script. To create an admin user, `cd` into the root Ion directory, then run:

    $ ./create-users.py --admin`<USERNAME>`

Run `./create-users.py --help` for help on using the script or for information on creating other types of users.

### Setting up Users using Python Shell

Currently, there are no default groups set up when you first install Ion. In order to grant yourself administrative privileges, you must be a member of the ``admin_all`` group.

To create and add yourself to this group, run the following commands (substituting your username for ``<USERNAME>``):

    $ ./manage.py shell_plus
    >>> user = User.objects.get_or_create(username="`<USERNAME>`")[0]
    >>> group = Group.objects.get_or_create(name="admin_all")[0]
    >>> user.groups.add(group)
    >>> user.is_superuser = True
    >>> user.save()

## Logging in to your Development Environment

The master password for development environments is `notfish`. Login with your username or `admin` and the master password to use your dev environment as an Intranet administrator.

## Setting up Files

You can find a list of file systems at ``intranet/apps/files/models.py``. To add these systems so that they appear on the Files page, run the statements found in the file. A sample is shown below:

    $ ./manage.py shell_plus
    >>> Host.objects.create(name="Computer Systems Lab", code="csl", address="remote.tjhsst.edu", linux=True)

# Advanced

## Backup or export database from Docker

Use these instructions to create a backup of your development environment's postgres database and, if desired, import it into another container or Docker instance running on a different machine.

### Overview

For the Ion development environment, database information is stored in [Docker volumes](https://docs.docker.com/storage/volumes/), under the name `docker_pgdata`. On a linux environment, volumes are stored in `/var/lib/docker/volumes`.

### Creating a backup volume

To create a backup of your volume on your local device, make a copy of `/var/lib/docker/volumes/docker_pgdata` to a location you will remember.

### Mount to another container

To create another database container with the postgres data mounted, run:

``docker run -it -v docker_pgdata:/var/lib/postgresql/data postgres:latest /bin/bash``

### Export to another machine or Docker instance

Follow these steps to export your data if you are creating a new development environment on a different machine. These steps assume you already have a running dev environment on the target machine.

Warning: you are likely to see errors that you will have to Google and solve yourself. Only do this if you have a substantial amount of data you need for your new environment; otherwise, it's easier to simply create another environment and add the data manually.

1. Create a copy of your data in case something goes wrong (see creating a backup volume section).
2. On the new machine, copy the postgres volume to your volume directory. Do this either through an USB, other file transfer method, or SSH. If using `scp`, run:
   ``scp -r  [USERNAME]@[HOST]:/var/lib/docker/volumes/docker_pgdata /var/lib/docker/volumes/``

Because you have copied over old configuration files to a new machine, the new postgres instance may think certain files are corrupted and not start. To correct this, do the following:

3. Create a container with the volume mounted:
   ``docker run -it -v /docker_pgdata:/var/lib/postgresql/data postgres:latest /bin/bash``
4. Run `apt update && apt install sudo`
5. Run `sudo -u postgres pg_resetwal /var/lib/postgresql/data`
6. Run `dd if=/dev/zero bs=1 count=8192 >> data/pg_xact/0000`
7. Exit the postgres container and restart your development environment. It should now contain all the data you had in your volume.
8. If something doesn't work, Google it...(and if you're feeling nice, add it here).

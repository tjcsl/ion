Creating Iodine fixtures
========================

Copy create_fixtures.py to Iodine
.. code-block:: bash
    $ python create_fixtures.py
    $ tar cvzf fixtures-20151014.tar.gz fixtures/
    $ scp fixtures-20151014.tar.gz ion:

Importing Iodine fixtures
=========================
Copy fixtures to Ion
.. code-block:: bash
    $ ksu
    $ cd /usr/local/www/intranet3
    $ cp /root/fixtures-20151014.tar.gz .
    $ tar xvzf fixtures-20151014.tar.gz

Load the users fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/users/users.json

Load the sponsors fixtures.
NOTE: manually fixed UID 503, which wasn't present (Ms. Gravitte, AP) by removing "user_id" from EighthSponsor entry
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/sponsors.json

Load the rooms fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/rooms.json

Load the blocks fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/blocks.json

Load the activities fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/activities.json

IMPORTANT!! Imported activities will have no "AID" field, so you must run:
.. code-block:: bash
    $ ./manage.py fix_aids

Load the scheduled activities fixtures.
Note: this takes around 3 minutes to import, much longer than the previous fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/scheduled_activities.json

Load the signups fixtures.
Note: this takes around 3 minutes to import, much longer than the previous fixtures.
.. code-block:: bash
    $ ./manage.py loaddata fixtures/eighth/signups.json

Load the announcements fixtures (optional).
.. code-block:: bash
    $ ./manage.py loaddata fixtures/announcements/announcements.json

Delete old blocks, and "Z-HAS NOT SELECTED AN ACTIVITY" activity. Make all "Z-" activities administrative.
.. code-block:: bash
    $ ./manage.py shell_plus
    Python 2.7.6 (default, Jun 22 2015, 17:58:13)
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> EighthBlock.objects.filter(date__lt="2015-09-01").delete()
    >>> EighthActivity.objects.get(id=999).delete()
    >>> EighthActivity.objects.filter(Q(name__istartswith="z-")|Q(name__istartswith="z -")).update(administrative=True)

    
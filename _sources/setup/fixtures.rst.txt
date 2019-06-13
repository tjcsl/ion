********
Fixtures
********

You can use fixtures to populate your database with test data.

Creating Ion fixtures
=====================

After you run the command below, the fixtures will be located in the fixtures folder.

.. code-block:: bash

    $ ./scripts/export_fixtures.sh

Importing Ion fixtures
======================

Place all of the fixture files in the fixtures folder and run the command below. You can use the ``-f`` flag to clear your database before importing.

.. code-block:: bash

    $ ./scripts/import_fixtures.sh

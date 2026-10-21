******************
Archiving accounts
******************

Archiving locks an account while retaining its user record and related data. Locked users lose
access through existing browser sessions on their next request, and their OAuth bearer tokens
are rejected while the account is locked.

To preview a CSV import, provide a UTF-8 CSV with a ``username`` column:

.. code-block:: bash

   python manage.py archive_users --filename users.csv

Add ``--run`` to archive the matching users after confirmation, or ``--run --confirm`` to skip
the prompt. Blank usernames are ignored; duplicate and missing usernames are reported. The
Django admin also provides an "Archive selected users" action.

The ``year_cleanup`` command requires exactly one of ``--delete-users``, ``--archive-users``,
or ``--no-user-changes`` to choose how graduated accounts are handled. The last option skips
account deletion and archiving; the other year-end cleanup steps still run. Both deletion and
archiving preserve graduated administrators as alumni with continued access.

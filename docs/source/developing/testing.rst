******************
Testing Ion
******************

Unit tests are hugely important to ensuring that Ion functions as expected. By writing and running tests before deploying every change, we can be much more confident that our new changes don't break the existing design in Ion. As such, every change that introduces a new feature should also include at least one unit test that corresponding to that feature.

Unit Tests
==========

For most modules, the unit tests go in ``intranet/apps/<module>/tests.py``. Eighth period uses several files under ``intranet/apps/eighth/tests/``; standalone ``test_*.py`` modules are also discovered. Shared test helpers live in ``intranet/test``.

.. _running-tests:

Running Tests Locally
=====================

Run application tests inside the Docker development environment. From the repository root, start the stack and inspect first-run setup:

.. code-block:: bash

    docker compose -f config/docker/docker-compose.yml up --build -d
    docker compose -f config/docker/docker-compose.yml logs -f django

With Python installed on the host, the development helper checks prerequisites before running tests:

.. code-block:: bash

    python3 scripts/dev.py doctor
    python3 scripts/dev.py test intranet.apps.polls
    python3 scripts/dev.py test intranet.apps.auth.tests.LoginViewTest -v 2
    python3 scripts/dev.py test

Test labels and options are forwarded to Django, and the helper returns the test runner's exit status. It does not start containers or install dependencies. It also verifies that Django mounts this checkout, since Ion's fixed container names are shared across worktrees. See :doc:`../setup/setup` if diagnostics report a setup problem.

Running Tests with Django's Test Runner (Recommended)
-----------------------------------------------------

The recommended way to run tests is using Django's built-in test runner, which is what CI uses:

.. code-block:: bash

    # Run all tests (this may take some time!)
    docker compose -f config/docker/docker-compose.yml exec -T django python ./manage.py test --noinput

    # Run tests for a specific app (in this case, polls)
    docker compose -f config/docker/docker-compose.yml exec -T django python ./manage.py test intranet.apps.polls --noinput

    # Run a specific test class
    docker compose -f config/docker/docker-compose.yml exec -T django python ./manage.py test intranet.apps.auth.tests.LoginViewTest --noinput

    # Run with verbose output, useful for debugging
    docker compose -f config/docker/docker-compose.yml exec -T django python ./manage.py test intranet.apps.polls --noinput -v 2

The test settings use an in-memory SQLite database and disable migrations. Docker's local settings can still require Redis for caches and other integrations. Test schema changes separately against PostgreSQL; the unit suite does not exercise migrations. CI also checks for missing migrations and runs migrations outside test mode.

Testing the Development Helper
------------------------------

The helper's command tests use the Python standard library and can run without Docker or Django:

.. code-block:: bash

    python3 -m unittest discover -s scripts -p test_dev.py -v

These tests simulate Docker responses to check diagnosis, checkout selection, argument forwarding, and exit codes. They do not verify the application or a live Docker stack.

Interactive Testing Shell
-------------------------

If you want to run multiple test commands, you can open an interactive shell with Docker:

.. code-block:: bash

    docker compose -f config/docker/docker-compose.yml exec django sh

    # then inside the container, run tests:
    ./manage.py test intranet.apps.polls --noinput

Coverage
========

Coverage information is auto-generated at `Coveralls <https://coveralls.io/github/tjcsl/ion>`. This is useful for finding files with insufficient coverage, so you can focus your test writing more accurately.

Writing Tests
=============

Looking at pre-existing tests can give you a good idea how to structure your tests. ``IonTestCase`` extends Django's ``TestCase`` with login, reauthentication, and admin helpers. Use ``SimpleTestCase`` for code that does not query the database. Here is a basic test layout:

.. code-block:: python

  from ...test.ion_test import IonTestCase

  class ModuleTest(IonTestCase):
    def test_module_function(self):
      # Put your tests here
      self.assertEqual(1, 1)

Every test should include comments that explain, almost in narrative form, what the test is doing and what the expected results are.

Generally, there are two ways that you test Ion's code. These are not comprehensive, but should work for most cases.
The first is calling methods directly; the second is making a GET or POST request to the view that you are interested in testing.
The best tests utilize both. After you do either/both of these to call the code, you should use assertions to see if the code behaved as expected.
A list of assertion options can be found `here <https://docs.python.org/3/library/unittest.html#assert-methods>`_.
A useful tool for making requests to the view is ``self.client``. More documentation on that can be found
`here <https://docs.djangoproject.com/en/stable/topics/testing/tools/>`_. Alternatively, just search through Ion's
testing files for examples of using ``self.client``.

Good Testing Examples
=====================

Ion has lots of tests; the following are examples of very well-written ones. Note the abundance of comments and the attention to detail. Test everything.

- `Polls <https://github.com/tjcsl/ion/blob/dev/intranet/apps/polls/tests.py>`_ - Note the throughness of the checks; assertions are made even when nothing should have changed.
- `Emailfwd <https://github.com/tjcsl/ion/blob/dev/intranet/apps/emailfwd/tests.py>`_ - Note the use of `self.client` and checking `messages` generated by the page.
- `Eighth <https://github.com/tjcsl/ion/tree/dev/intranet/apps/eighth/tests>`_ - ``eighth`` is the most complicated app in Ion and thus has the most varied examples of testing methods to check out.

References
==========

- `Django Testing Guide <https://docs.djangoproject.com/en/stable/topics/testing/>`_
- `Python unittest documentation <https://docs.python.org/3/library/unittest.html>`_
- `Code Coverage <https://coveralls.io/github/tjcsl/ion>`_
- `Python Unit Testing Assert Methods <https://docs.python.org/3/library/unittest.html#assert-methods>`_
- `Testing Exceptions <https://docs.djangoproject.com/en/stable/topics/testing/tools/#exceptions>`_

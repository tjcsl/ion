******************
Testing Ion
******************

Unit Tests
==========

You will want to write your tests for each module in ``intranet/apps/<module>/tests.py``.
Testing functionality that is useful for multiple tests can be found in ``intranet/test``.

Running Tests
=============

To actually execute tests, run ``./setup.py test``.
Note that this deletes and re-creates the db from scratch each time,
so you may want to pass the ``-k`` option when developing tests as it significantly reduces run-time.

Coverage
========

Coverage information is auto-generated at `Coveralls <https://coveralls.io/github/tjcsl/ion>`_
This is useful for finding files with insufficient coverage,
so you can focus your test writing more accurately.

Writing Tests
=============

Looking at pre-existing tests can give you a good idea how to structure your tests.
The ``IonTestCase`` class is a wrapper around the standard Django test class.
It handles some ion-specific logic, such as mocking out ldap queries.
Here is an bare-bones example of the basic layout for a test:

.. code-block:: python

  from ...test.ion_test import IonTestCase

  class ModuleTest(IonTestCase):
    def test_module_function(self):
      # Put your tests here
      self.assertEqual(1, 1)

References
==========

- `Django Testing Guide <https://docs.djangoproject.com/en/1.11/topics/testing>`_.
- `Python unittest documentation <https://docs.python.org/3/library/unittest.html>`_.
- `Code Coverage <https://coveralls.io/github/tjcsl/ion>`_.

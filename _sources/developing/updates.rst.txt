*************************
Keeping things up-to-date
*************************

Vendored Libraries
==================

- `CKEditor <http://ckeditor.com/builder/download/601464899923a382ecb1b77b655402c3>_`
- `datetimepicker <https://github.com/xdan/datetimepicker/releases>_`
- jQuery-UI:
  *Note: This has very specific CSL customizations)*
- `Messenger <https://github.com/HubSpot/messenger/releases>_`
- `selectize <https://github.com/selectize/selectize.js/releases>_`
- `sortable <https://github.com/HubSpot/sortable/releases>_`

Updating Top-level Requirements
================================

If any commit changes the direct dependencies of Ion, you must update `the requirements documentation<developing/requirements>`_ to reflect the changes to Ion's dependencies. That page is organized into sections for each dependency, with a line for the package's source URL, a general description of the package, the usage of the package in Ion, and the package's license.

For example, here is a valid section:

.. code-block:: text
    sentry-sdk
    -----------------
    https://github.com/getsentry/sentry-python

    This package provides a Python SDK for the Sentry monitoring suite.

    It is used to collect and report information to report to Sentry in production.

    LICENSE: 2-clause BSD

Additional lines may be added to identify needed actions regarding the package.

Requirements for Dependencies
==============================

**All** dependencies to Ion must be licensed under an `OSI-approved open source license <https://opensource.org/licenses>`_.  The use of the package must be compatible with the terms of the GNU General Public License v2 (or later version).

**All** direct dependencies to Ion must be reported in the requirements documentation.

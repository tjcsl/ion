**********
Intranet 3
**********
.. image:: https://travis-ci.org/tjcsl/ion.svg?branch=master
    :target: https://travis-ci.org/tjcsl/ion
    :alt: Travis CI

.. image:: https://codeclimate.com/github/tjcsl/ion/badges/gpa.svg
   :target: https://codeclimate.com/github/tjcsl/ion
   :alt: Code Climate

.. image:: https://coveralls.io/repos/tjcsl/ion/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/tjcsl/ion?branch=master
    :alt: Coverage

.. image:: https://readthedocs.org/projects/ion/badge/?version=latest
    :target: http://ion.readthedocs.org/en/latest
    :alt: Docs

Version 3.0.0

Intranet3 (Ion) is the next-generation Intranet platform for `TJHSST 
<https://www.tjhsst.edu/>`_. Using Python, Django, Redis, Postgres, and many other technologies, Ion was developed from the ground up to be simple, well-documented, and extensible.

Documentation (in RestructuredText format) is available inside the "docs" folder or at http://tjcsl.github.io/ion/ publicly on the web.

**What does the TJ Intranet do?** Ion allows students, teachers, and staff at TJHSST to access student information, manage activity signups, and view information on news and events. `Read more about how Ion is used at Thomas Jefferson <https://ion.tjhsst.edu/about>`_.

**Ion now uses Python 3.** Python 3.4 is now currently used in both production and testing environments. If you already have a Vagrant environment set up with Python 2, re-run ``config/provision_vagrant.sh`` to update dependencies.

**How can I create a testing environment?** Read the section on `Setting up Vagrant <http://tjcsl.github.io/ion/setup/vagrant.html>`_ in the documentation. Ask a TJ Sysadmin for VPN access and tokens needed to connect to our servers.

**Where can I report a bug?**

* Most bugs and feature requests should be submitted through `GitHub Issues <https://github.com/tjcsl/ion/issues>`_.
* Security-related or TJ CSL-specific issues should be submitted on `Bugzilla <http://bugs.tjhsst.edu/>` or emailed to `intranet@tjhsst.edu <mailto:intranet@tjhsst.edu>`_.


Current Intranet maintainer: `James Woglom <https://github.com/jwoglom>`_ (TJ 2016)

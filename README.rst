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

.. image:: https://api.codacy.com/project/badge/grade/24f9f397f4624c548782b5f78bcc1d51
    :target: https://www.codacy.com/app/pefoley2/ion
    :alt: Codacy

.. image:: https://readthedocs.org/projects/ion/badge/?version=latest
    :target: http://ion.readthedocs.org/en/latest
    :alt: Docs

Version 3.0.0

Intranet3 (Ion) is the next-generation Intranet platform for `TJHSST 
<https://www.tjhsst.edu/>`_. Using Python, Django, Redis, Postgres, and many other technologies, Ion was developed from the ground up to be simple, well-documented, and extensible.

Documentation (in RestructuredText format) is available inside the "docs" folder or at https://ion.readthedocs.org/ publicly on the web.

**What does the TJ Intranet do?** Ion allows students, teachers, and staff at TJHSST to access student information, manage activity signups, and view information on news and events. `Read more about how Ion is used at Thomas Jefferson <https://ion.tjhsst.edu/about>`_.

**Ion now requires Python 3.4+** Python 3.4 is currently used in both production and testing environments. If you already have a Vagrant environment set up with Python 2, re-run ``config/provision_vagrant.sh`` to update dependencies.

**How can I create a testing environment?** Read the section on `Setting up Vagrant <https://ion.readthedocs.org/en/latest/setup/vagrant.html>`_ in the documentation. Ask a TJ Sysadmin for VPN access and tokens needed to connect to our servers.

**Why is my build failing?** A PEP 8 syntax checker is set as a post-commit hook. You can add a pre-commit hook to warn you by running ``flake8 --install-hook``. Ensure that your code follows those guidelines by running something like this in the root of the repository: ``autopep8 -ir --max-line-length=200 .``

**Where can I report a bug?**

* Most bugs and feature requests should be submitted through `GitHub Issues <https://github.com/tjcsl/ion/issues>`_.
* Security-related or TJ CSL-specific issues should be submitted on `Bugzilla <http://bugs.tjhsst.edu/>`_ or emailed to `intranet@tjhsst.edu <mailto:intranet@tjhsst.edu>`_.


Current Intranet maintainer: `James Woglom <https://github.com/jwoglom>`_ (TJ 2016)

*************************
TJ Intranet Documentation
*************************

Intro
=====

Intranet3 (Ion) is the next-generation Intranet platform for TJHSST. Using Python, Django, Redis, Postgres, and many other technologies, Ion was developed from the ground up to be simple, well-documented, and extensible.

Contents
========

.. toctree::
    :maxdepth: 2
    :hidden:

    setup/index
    architecture/index
    developing/index
    sourcedoc/modules
    administration/index


Setup
-----

- :doc:`Setting up the server<setup/server>`
- :doc:`Setting up a Vagrant development environment<setup/vagrant>`
- :doc:`Setting up fixtures from Iodine<setup/fixtures>`


Architecture
------------

Ion uses Django, Redis, Postgres, and many other Python frameworks and tools.

See the :doc:`Architecture documentation<architecture/index>`.



Developing for Intranet
-----------------------
- :doc:`Workflow<developing/workflow>`
- :doc:`Coding Style Guide<developing/styleguide>`
- :doc:`Test Writing Guide<developing/testing>`

Using Intranet as a Developer
-----------------------------
- `API Root <https://ion.tjhsst.edu/api/>`_
- `API Demo <https://www.tjhsst.edu/~2016jwoglom/ion-api-demo.html>`_
- `OAuth Documentation<developing/oauth>`
- `OAuth Demo <https://www.tjhsst.edu/~2016jwoglom/ionoauth/>`_

Source Code Documentation
-------------------------
.. code-block:: rst

  Example documentation for Django settings :django:setting:`ROOT_URLCONF`
  and python objects :class:`threading.Thread`

More details can be found at `Sphinx Documentation <http://sphinx-doc.org/markup/index.html>`_

Go to the :doc:`Source Code Documentation<sourcedoc/intranet>`

Administration
--------------

How to use Intranet



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


*****************
Ion Requirements
*****************

Intranet 3 (Ion) depends on a variety of third-party libraries and packages

Explicit Requirements
=====================

argon2-cffi
-----------------
https://github.com/hynek/argon2-cffi

This package provides CFFI-based Argon2 Python bindings.

It is used to provide bindings for Argon2 hashing of the Ion master password.

LICENSE: MIT

autobahn
-----------------
https://github.com/crossbario/autobahn-python

This package provides `WebSocket <http://tools.ietf.org/html/rfc6455>_` & `Web Appplication Messaging Protocol (WAMP) <http://wamp-proto.org/>_` support.

It provides WebSocket support for Ion.

LICENSE: MIT

babel
-----------------
https://github.com/python-babel/babel

This package provides an integrated collection of utilities that assist with internationalizing and localizing Python applications.

It provides localization support for Jinja templates in Ion.

LICENSE: 3-clause BSD

bcrypt
------------------
https://github.com/pyca/bcrypt

This package provides bcrypt hashing support.

It is used to hash the Ion master password.

LICENSE: Apache License 2.0

beautifulsoup4
------------------
https://github.com/waylan/beautifulsoup

This package provides support for parsing web pages.

It is used to parse the FCPS emergency webpage.

LICENSE: MIT

bleach
-----------------
https://github.com/mozilla/bleach

This package provides HTML sanitization that escapes or strips markup and attributes.

It is used to clean up tags, attributes, and styles in input from polls, announcements, and other forms.

LICENSE: Apache License 2.0

celery
-----------------
https://github.com/celery/celery

This package provides an asynchronous task queue/job queue based on distributed message passing. It is focused on real-time operation, but supports scheduling as well.

It provides the task queue that powers long-running operations like sending mass emails.

LICENSE: 3-clause BSD

certifi
-----------------
https://github.com/certifi/python-certifi

This package provides a collection of trusted root certificates.

FIXME

LICENSE: Mozilla Public License 2.0

channels
------------------
https://github.com/django/channels

This package brings WebSocket, long-poll HTTP, task offloading and other async support in a Django-like framework.

It provides WebSocket support for Ion.

LICENSE: 3-clause BSD

channels-redis
------------------
https://github.com/django/channels_redis

This package provides a redis channel layer backend for Django Channels

It provides the backend for ASGI requests over Django Channels.

LICENSE: 3-clause BSD

contextlib2
-------------------
https://github.com/jazzband/contextlib2

This package provides a backport of ``contextlib`` from Python 3.5 and adds new functionality.

FIXME

LICENSE: Python Software Foundation License

cryptography
------------------
https://github.com/pyca/cryptography

This package provides cryptographic recipes and primitives.

FIXME

LICENSE: Apache License 2.0 or 3-clause BSD

decorator
------------------
https://github.com/micheles/decorator

This package provides definitions of signature-preserving function decorators and decorator factories.

FIXME

LICENSE: 2-clause BSD

django
------------------
https://github.com/django/django

Django is a high-level Python Web framework that encourages rapid development and clean, pragmatic design. 

It is used as our web framework.

LICENSE: 3-clause BSD

django-cacheops
-------------------
https://github.com/Suor/django-cacheops

This package is a Django app that supports automatic or manual queryset caching into a Redis ORM cache.

It is used for queryset caching into a Redis databse.

LICENSE: 3-clause BSD

django-cors-headers
--------------------
https://github.com/ottoyiu/django-cors-headers

This package is a Django app that adds Cross-Origin Resource Sharing (CORS) headers to responses

It is used to support when absolutely necessary cross-origin requests.

LICENSE: MIT

django-debug-toolbar
--------------------
https://github.com/jazzband/django-debug-toolbar

This package is a Django app that provides a configurable set of panels that display various debug information about the current request/response.

It is used in Django's debug mode to help diagnose request/response issues.

LICENSE: 3-clause BSD

django-extensions
------------------
https://github.com/django-extensions/django-extensions

This package is a Django app that adds command extensions.

It is used to provide additional commands for Django.

LICENSE: MIT

django-formtools
----------------
https://github.com/django/django-formtools

This package is a Django app that provides abstractions for Django forms.

It is used to provide a SessionWizardView, a wizard used in eighth admin.

NEEDSRELEASE

LICENSE: 3-clause BSD

django-inline-svg
------------------
https://github.com/mixxorz/django-inline-svg

This package is a Django app that provides a template tag for inline SVGs.

It is used to embed SVGs (like in the ``bus`` app).

NEEDSRELEASE

LICENSE: MIT

django-maintenance-mode
-------------------------
https://github.com/fabiocaccamo/django-maintenance-mode

This package is a Django app that displays a 503 page when maintenance mode is enabled.

It is used to enable maintenance on Ion when necessary.

LICENSE: MIT

django-oauth-toolkit
-----------------------
https://github.com/jazzband/django-oauth-toolkit

This package is a Django app that provides all the endpoints, data and logic needed to add OAuth2 capabilities to your Django projects.

It is used to provide Ion OAuth2 support.

NEEDSNEWER (needs Django 2.0)

LICENSE: 2-clause BSD

django-pipeline
-----------------------
https://github.com/jazzband/django-pipeline

This package provides both CSS and JavaScript concatenation and compression, built-in JavaScript template support, and optional data-URI image and font embedding.

It provides the ``stylesheet`` templatetag and compresses our CSS.

NEEDSRELEASE

LICENSE: MIT

django-prometheus
----------------------
https://github.com/korfuri/django-prometheus

This package is a Django app that provides support for exporting basic monitoring metrics from Django.

It is used to export prometheus metrics at ``/prometheus/metrics``.

LICENSE: Apache License 2.0

django-redis-cache
---------------------
https://github.com/sebleier/django-redis-cache

This package provides the redis backend cache. 

FIXME: Needs more specific info

LICENSE: 3-clause BSD

django-redis-sessions
----------------------
https://github.com/martinrusev/django-redis-sessions

This package provides a redis backend for Django sessions.

It is used to store session information in redis cache.

NEEDSRELEASE

LICENSE: 3-clause BSD

django-request-logging-redux
-----------------------------
https://github.com/tarkatronic/django-requestlogging

This package provides a logging filter and middleware to add information about the current request to the logging record.

It is used to record information about requests to the console, file, and Sentry log.

NEEDSRELEASE

LICENSE: 3-clause BSD

django-simple-history
-------------------------
https://github.com/treyhunner/django-simple-history

This package stores Django model state on every create/update/delete.

It is used to preserve a history of changes to specified eighth models.

LICENSE: 3-clause BSD

django-widget-tweaks
-----------------------
https://github.com/jazzband/django-widget-tweaks

This package provides support to tweak the form field rendering in templates,

It is used in the ``schedule_activity`` template to tweak rendering of form fields.

LICENSE: MIT

django-rest-framework
-----------------------
https://github.com/encode/django-rest-framework

This package provides a powerful and flexible toolkit for building Web APIs.

It is used for the Ion API.

LICENSE: 3-clause BSD

docutils
---------
https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/

This package provides a modular system for processing documentation into useful formats, such as HTML, XML, and LaTeX. 

It is an optional dependency for admindocs and setuptools.

Fabric3
-------
https://github.com/mathiasertl/fabric/

This package provides a basic suite of operations for executing local or remote shell commands (normally or via sudo) and uploading/downloading files, as well as auxiliary functionality such as prompting the running user for input, or aborting execution.

It is used to manage the Ion application in both developement and production (see ``fabfile.py``)

NEEDSRELEASE

LICENSE: 2-clause BSD

flower
-------
https://github.com/mher/flower

This package provides a real-time monitor and web admin for the Celery distributed task queue.

It is used to help administrators and developers monitor their Celery task queues.

LICENSE: 3-clause BSD

gunicorn
---------
https://github.com/benoitc/gunicorn

This package provides a Python WSGI HTTP Server for UNIX.

FIXME

OBSOLETE: needs verification

LICENSE: MIT

hiredis
----------
https://github.com/redis/hiredis-py

This package a Python wrapper for hiredis. hiredis is a library for redis.

It is directly used as a ``HiredisParser`` in the redis cache.

LICENSE: 3-clause BSD

ipython
----------
https://github.com/ipython/ipython

This package provides a rich toolkit to help you make the most of using Python interactively, including a powerful interactive Python shell

It is directly used by the interactive shell for ``python manage.py shell_plus``.

LICENSE: 3-clause BSD

objgraph
----------
https://github.com/mgedmin/objgraph

This package is a module that lets you visually explore Python object graphs.

It is used by ``flower`` to draw graphs.

LICENSE: MIT

pexpect
----------
https://github.com/pexpect/pexpect

This package provides the ability to spawn child applications; controll them; and respond to expected patterns in their output. It allows your script to spawn a child application and control it as if a human were typing commands.

It is used to help interact with Kerberos password authentications and changes.

LICENSE: ISC License

psycopg2
----------
https://github.com/psycopg/psycopg2

This package provides an adapter for PostgreSQL.

It is used to connect to the PostgreSQL database from the Django application.

LICENSE: GNU Lesser General Public License v 3.0+

pycryptodome
--------------
https://github.com/Legrandin/pycryptodome

This package provides low-level cryptographic primitives.

It is used to encrypt the password for Ion Files. The key is stored as a client-side cookie and the IV/ciphertext is stored a server-side session variable.

LICENSE: 2-clause BSD

pysftp
-------
https://bitbucket.org/dundeemt/pysftp/src/default/

This package provides a simple interface to the Secure File Transport Protocol (SFTP).

It is used by Ion Files to access remote servers/files.

LICENSE: 3-clause BSD

python-dateutil
---------------
https://github.com/dateutil/dateutil

This package provides powerful extensions to the standard datetime module

It (``datetime.relativedelta``) is used to compute deltas between datetime objects throughout the codebase.

LICENSE: Apache License 2.0 (based on code that is 3-clause BSD)

python-gssapi
---------------
https://github.com/sigmaris/python-gssapi

This package provides an object-oriented interface to GSSAPI for Python.

It is used for Kerberos authentication.

OBSOLETE: need to update is from 2015

LICENSE: MIT

python-magic
--------------
https://github.com/ahupp/python-magic

This package is a wrapper to the libmagic file type identification library

It is used to identify the file type for Ion Printing.

NEEDSRELEASE

LICENSE: MIT

reportlab
-----------
https://bitbucket.org/rptlab/reportlab/src/default/

This package allows rapid creation of rich PDF documents, and also creation of charts in a variety of bitmap and vector formats.

It is used to help generate PDFs in the eighth admin.

LICENSE: 3-clause BSD

requests
---------
https://github.com/kennethreitz/requests

This package is a HTTP library for Python.

It is used to fetch the FCPS emergency webpage.

LICENSE: Apache License 2.0

requests-oauthlib
------------------
https://github.com/requests/requests-oauthlib

This package provides OAuth library support for Python Requests.

It is currently used to perform OAuth1a authentication to Twitter.

LICENSE: ISC License

sentry-sdk
-----------------
https://github.com/getsentry/sentry-python

This package provides a Python SDK for the Sentry monitoring suite.

It is used to collect and report information to report to Sentry in production.

LICENSE: 2-clause BSD

setuptools-git
------------------
https://github.com/msabramo/setuptools-git

This package provides a plugin for setuptools that enables git integration.

It is used by our ``setup.py``.

NEEDSMAINTAINER

LICENSE: 3-clause BSD

Sphinx
-----------------
https://github.com/sphinx-doc/sphinx

This package provides a tool that makes it easy to create intelligent and beautiful documentation for Python projects.

It is used to document Ion.

LICENSE: 2-clause BSD

sphinx-bootstrap-theme
-------------------------
https://github.com/ryan-roemer/sphinx-bootstrap-theme

This package provides a bootstrap theme for Sphinx.

It is used as the theme for the Ion docs.

LICENSE: MIT

************
Architecture
************

Ion takes advantage of various technologies in order to provide the best, fastest, safest, and most reliable experience for our users.

Technologies
============

Django
------
We use `Django <https://www.djangoproject.com/>`_ as our web framework (written in Python).  We chose it for its wealth of documentation, supportive community, stability, ease of development, and vast array of third-party libraries that meet our needs.
Django has allowed us to deploy faster, onboard new web developers faster, and has served the Intranet team well.


REST API
--------
We use `Django Rest Framework (DRF) <https://www.django-rest-framework.org/>`_ for our REST API. In particular, DRF provides the basic framework for quickly creating secure APIs with a decent web interface. It is also known as an industry standard.

Redis
-----
`Redis <https://redis.io/>`_ is an in-memory data store that we use currently use to cache session information and other information in memory. We use `django-cacheops <https://github.com/Suor/django-cacheops>`_ as an ORM cache for our models and `django-redis-sessions <https://github.com/martinrusev/django-redis-sessions>`_ as a in-memory session cache for user sessions.

PostgreSQL
----------
We use `PostgreSQL <https://www.postgresql.org/>`_ for our production and development databases.  PostgreSQL is an open-source relational SQL database that has an array of tooling behind it and is strongly supported by Django and the wider web development community. In addition, PostgreSQL is known for its "reliability, feature robustness, and performance."

Daphne
----------
We use `Daphne <https://github.com/django/daphne/>`_ for our production Django Channels HTTP/WebSocket server. We serve stuff over ASGI for WebSockets (bus) and Daphne allows us to run our application in production simply.

Celery
------
We use `Celery <http://www.celeryproject.org/>`_ to run background tasks such as sending emails asynchronously.

RabbitMQ
--------
We use `RabbitMQ <https://www.rabbitmq.com/>`_ as a message broker for Celery (Celery claims to support `Redis <#redis>`_, but attempts to get it working were unsuccessful).

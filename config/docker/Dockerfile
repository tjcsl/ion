FROM python:3.11-alpine3.22

ENV TZ America/New_York
ENV C_FORCE_ROOT true

COPY config/krb5.conf /etc/krb5.conf
COPY requirements.txt .
COPY requirements-dev.txt .

RUN apk update && \
    apk add bash git curl build-base libpq-dev freetype-dev libffi-dev ruby-full libmagic krb5 rsync nodejs npm tzdata libxml2-dev libxslt-dev && \
    npm install -g sass && \
    ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    pip3 install -Ir requirements.txt && \
    pip3 install -Ir requirements-dev.txt && \
    rm requirements.txt requirements-dev.txt

WORKDIR /ion

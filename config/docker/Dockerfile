FROM alpine:latest

ENV TZ America/New_York
ENV C_FORCE_ROOT true

COPY config/krb5.conf /etc/krb5.conf
COPY requirements.txt .

RUN apk update && \
    apk add bash git curl python3 python3-dev py3-pip build-base libpq-dev freetype-dev ruby-full libmagic krb5 kinit rsync nodejs npm && \
    npm install -g sass && \
    pip3 install pipenv && \
    ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    pip3 install -I -r requirements.txt && \
    pip3 install -I -r requirements-dev.txt && \
    rm requirements.txt && \
    rm requirements-dev.txt

WORKDIR /ion

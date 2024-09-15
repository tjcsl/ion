FROM python:3.8.19-alpine3.18

ENV TZ=America/New_York
ENV C_FORCE_ROOT=true
ENV UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PROJECT_ENVIRONMENT=/venv

COPY config/krb5.conf /etc/krb5.conf
COPY pyproject.toml .
COPY uv.lock .

COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /bin/uv

RUN apk update && \
    apk add bash git curl build-base libpq-dev freetype-dev libffi-dev ruby-full libmagic krb5 kinit rsync nodejs npm tzdata libxml2-dev libxslt-dev && \
    npm install -g sass && \
    ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    uv sync

WORKDIR /ion

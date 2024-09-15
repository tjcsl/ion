FROM python:3.8.19-alpine3.18

ENV TZ=America/New_York
ENV C_FORCE_ROOT=true

COPY config/krb5.conf /etc/krb5.conf
COPY pyproject.toml .

COPY --from=ghcr.io/astral-sh/uv:0.4.10 /uv /bin/uv

RUN apk update && \
    apk add bash git curl build-base libpq-dev freetype-dev libffi-dev ruby-full libmagic krb5 kinit rsync nodejs npm tzdata libxml2-dev libxslt-dev && \
    npm install -g sass && \
    ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # note that this also includes dev dependencies: pass --no-dev to exclude them
    uv sync --no-install-project

ENV PATH="/.venv/bin:${PATH}"

WORKDIR /ion

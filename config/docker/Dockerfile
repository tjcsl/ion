FROM python:3.8.19

ENV TZ=America/New_York
ENV C_FORCE_ROOT=true

COPY config/krb5.conf /etc/krb5.conf
COPY requirements.txt .
COPY requirements-dev.txt .

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash \
        git \
        curl \
        build-essential \
        libpq-dev \
        libfreetype6-dev \
        libffi-dev \
        ruby-full \
        libmagic-dev \
        krb5-user \
        rsync \
        nodejs \
        npm \
        tzdata \
        libxml2-dev \
        libxslt-dev && \
    npm install -g sass && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    pip3 install -Ir requirements.txt && \
    pip3 install -Ir requirements-dev.txt && \
    rm requirements.txt requirements-dev.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /ion

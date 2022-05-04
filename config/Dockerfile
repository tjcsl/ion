FROM ubuntu:latest

ENV TZ America/New_York
ENV C_FORCE_ROOT true

COPY config/krb5.conf /etc/krb5.conf
COPY requirements.txt .

RUN apt-get -y update && \
    apt-get -y clean && \
    apt-get -y install git python3 python3-pip python-is-python3 \
    libpq-dev ruby-full rubygems libmagic1 && gem install sass && \
    pip3 install pipenv && \
    ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install krb5-user kinit && \
    pip3 install -r requirements.txt && \
    rm requirements.txt

WORKDIR /ion

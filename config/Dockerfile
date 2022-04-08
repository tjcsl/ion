FROM ubuntu:latest
RUN apt-get -y update && \
apt-get -y clean && \
apt-get -y install git python3 python3-pip python-is-python3 \
libpq-dev ruby-full rubygems && gem install sass && pip3 install pipenv
ENV TZ America/New_York
ENV C_FORCE_ROOT true
RUN ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY config/krb5.conf /etc/krb5.conf
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install krb5-user kinit
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN rm requirements.txt
WORKDIR /ion

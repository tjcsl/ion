FROM ubuntu:latest
RUN apt-get -y update && apt-get -y clean && apt-get -y install sudo git python3 python3-pip python-is-python3 libpq-dev ruby-full rubygems && gem install sass
ENV TZ America/New_York
RUN ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get -y install kinit
COPY config/krb5.conf /etc/krb5.conf
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install krb5-user
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
EXPOSE 8080
WORKDIR /ion
ENTRYPOINT ["/bin/bash","-c","chmod +x config/entrypoint.sh && config/entrypoint.sh"]
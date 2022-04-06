FROM ubuntu:latest
RUN apt-get -y update && apt-get -y clean 
RUN apt-get -y install sudo
RUN apt-get -y install git
RUN sudo apt-get -y install python3
RUN sudo apt-get -y install python3-pip
RUN sudo apt-get -y install python-is-python3
RUN sudo apt-get -y install libpq-dev 
RUN sudo apt-get -y install ruby-full rubygems
RUN gem install sass
ENV TZ America/New_York
RUN ln -s /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN sudo apt-get -y install kinit
COPY config/krb5.conf /etc/krb5.conf
RUN sudo DEBIAN_FRONTEND=noninteractive apt-get -y install krb5-user
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
EXPOSE 8080
WORKDIR /ion
ENTRYPOINT ["/bin/bash","-c","chmod +x config/entrypoint.sh && config/entrypoint.sh"]

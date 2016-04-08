#!/bin/bash

function devconfig() {
    python3 -c "
import json
f = open('/home/vagrant/intranet/config/devconfig.json', 'r')
print(json.load(f)['$1'])
f.close()"
}

apt-get update

# Timezone
timedatectl set-timezone America/New_York

# DNS
echo 198.38.16.8 iodine-ldap.tjhsst.edu >> /etc/hosts

# Kerberos
cp intranet/config/krb5.conf /etc/krb5.conf
apt-get -y install heimdal-clients

# Python
apt-get -y install python3-pip
pip3 install virtualenvwrapper
apt-get -y install python3-dev
apt-get -y install libjpeg8-dev

# LDAP
apt-get -y install ldap-utils
apt-get -y install libldap2-dev
apt-get -y install libsasl2-dev
apt-get -y install libssl-dev
apt-get -y install libsasl2-modules-gssapi-mit

# LDAP-GSSAPI
apt-get -y install libkrb5-dev

# Git
apt-get -y install git
sudo -i -u vagrant git config --global user.name "$(devconfig name)"
sudo -i -u vagrant git config --global user.email "$(devconfig email)"

# CUPS Printing
apt-get -y install cups
apt-get -y install cups-bsd
apt-get -y install cups-client
echo "ServerName cups2.csl.tjhsst.edu" > /etc/cups/client.conf

# Shell
cp intranet/config/bash_completion.d/fab /etc/bash_completion.d/fab
if ! grep "ion_env_setup.sh" /etc/bash.bashrc > /dev/null; then
    echo "source /etc/ion_env_setup.sh" >> /etc/bash.bashrc
fi
cp intranet/config/ion_env_setup.sh /etc/ion_env_setup.sh
touch .bash_history

# Utils
apt-get -y install htop
apt-get -y install glances

# CSS
apt-get -y install ruby-sass

# PostsgreSQL
apt-get -y install postgresql
apt-get -y install postgresql-contrib
apt-get -y install libpq-dev
sqlcmd(){
    sudo -u postgres psql -U postgres -d postgres -c "$@"
}
sqlcmd "CREATE DATABASE ion;"
sqlcmd "CREATE USER ion PASSWORD '$(devconfig sql_password)';"
sed -Ei "s/(^local +all +all +)peer$/\1md5/g" /etc/postgresql/9.3/main/pg_hba.conf
service postgresql restart

# Redis
wget --progress dot:giga http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make install
cd utils
echo | ./install_server.sh
cd ../..
rm -rf redis-stable redis-stable.tar.gz

# Ion
grep -qs AUTHUSER_PASSWORD intranet/intranet/settings/secret.py || echo "AUTHUSER_PASSWORD = \"$(devconfig ldap_simple_bind_password)\"" >> intranet/intranet/settings/secret.py
master_pwd='swordfish'
master_pwd_hash='pbkdf2_sha256$15000$GrqEVqNcFQmM$V55xZbQkVANeKb9BPaAV3vENYVd6yadJ5fjsbWnFpo0='
grep -qs MASTER_PASSWORD intranet/intranet/settings/secret.py || echo -e "\n# \"$master_pwd\"\nMASTER_PASSWORD = \"$master_pwd_hash\"" >> intranet/intranet/settings/secret.py

sudo -i -u vagrant bash -c "
    source /etc/ion_env_setup.sh &&
    mkvirtualenv --python=python3.4 ion && workon ion &&
    pip install -r intranet/requirements.txt
"
source .virtualenvs/ion/bin/activate
cd intranet
mkdir -p uploads
./manage.py migrate --noinput
cd ..
chown -R vagrant: /home/vagrant

mkdir /var/log/ion
chown -R vagrant: /var/log/ion

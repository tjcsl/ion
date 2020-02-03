#!/bin/bash
set -e

function devconfig() {
    python3 -c "
import json
with open('/home/vagrant/intranet/config/devconfig.json', 'r') as f:
    print(json.load(f)['$1'])"
}

sudo su - vagrant
cd /home/vagrant
sudo chown -R vagrant: /home/vagrant/.ssh
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get -y dist-upgrade
# Timezone
timedatectl set-timezone America/New_York

# Kerberos
cp intranet/config/krb5.conf /etc/krb5.conf
apt-get -y install krb5-user

# Python
apt-get -y install python3-pip
pip3 install -U virtualenvwrapper
apt-get -y install python3-dev
apt-get -y install libjpeg8-dev
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
if [[ -x "$(which gem)" ]]; then
    echo
    echo "Uninstalling deprecated Ruby Sass (and Ruby)"
    echo
    gem uninstall sass
    if dpkg -s rubygems; then
        apt-get -y remove rubygems
    else
        apt-get -y remove rubygems-integration
    fi
    apt-get -y remove ruby-dev
fi
apt-get -y install npm nodejs
npm -g install sass

# PostsgreSQL
apt-get -y install postgresql
apt-get -y install postgresql-contrib
apt-get -y install libpq-dev
sqlcmd(){
    sudo -u postgres psql -U postgres -d postgres -c "$@"
}
sqlcmd "CREATE DATABASE ion;" || echo Database already exists
sqlcmd "CREATE USER ion PASSWORD '$(devconfig sql_password)';" || echo Database user already exists
sed -Ei "s/(^local +all +all +)peer$/\1md5/g" /etc/postgresql/10/main/pg_hba.conf
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

# RabbitMQ
apt-get -y install rabbitmq-server
# RabbitMQ starts epmd processes that don't get killed properly. This fixes it.
# Source: https://bugs.archlinux.org/task/55842
mkdir -p /etc/systemd/system/rabbitmq-server.service.d
echo $'[Unit]\nRequires=epmd.service\nAfter=epmd.service' >/etc/systemd/system/rabbitmq-server.service.d/override.conf

# Ion
master_pwd='swordfish'
master_pwd_hash='pbkdf2_sha256$15000$GrqEVqNcFQmM$V55xZbQkVANeKb9BPaAV3vENYVd6yadJ5fjsbWnFpo0='
grep -qs MASTER_PASSWORD intranet/intranet/settings/secret.py || echo -e "\n# \"$master_pwd\"\nMASTER_PASSWORD = \"$master_pwd_hash\"" >> intranet/intranet/settings/secret.py

sudo -i -u vagrant bash -c "
    source /etc/ion_env_setup.sh &&
    mkvirtualenv --python=python3 ion && workon ion &&
    pip install -U -r intranet/requirements.txt
"
source .virtualenvs/ion/bin/activate
cd intranet
mkdir -p uploads
./manage.py migrate --noinput
./manage.py collectstatic --noinput

mkdir -p /var/log/ion
chown -R vagrant: /var/log/ion

#!/bin/sh

# System
sudo apt-get update
sudo apt-get install krb5-user
sudo apt-get install git

# Python
sudo apt-get install python-pip
sudo pip install virtualenv
sudo pip install virtualenvwrapper


# Shell
sudo cp /vagrant/config/bash_completion.d/fab /etc/bash_completion.d/fab
grep "ion_env_setup.sh" ~/.bashrc || (echo "source .ion_env_setup.sh" >> ~/.bashrc)
cp /vagrant/ion_env_setup.sh ~/.ion_env_setup.sh

# PostsgreSQL
sudo apt-get install postgresql postgresql-contrib


# Redis

# Elasticsearch

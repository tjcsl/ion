#!/bin/bash
export VIRTUAL_ENV="/usr/local/virtualenvs/ion"
cd /usr/local/www/intranet3
/usr/local/virtualenvs/ion/bin/python /usr/local/www/intranet3/manage.py signup_status_email --only-tomorrow --silent
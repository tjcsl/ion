#!/bin/bash
cd /usr/local/www/intranet3
VIRTUAL_ENV="/usr/local/virtualenvs/ion" /usr/local/virtualenvs/ion/bin/python /usr/local/www/intranet3/manage.py signup_status_email --only-today --silent
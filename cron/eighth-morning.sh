#!/bin/bash
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py signup_status_email --only-today --silent
#!/bin/bash
# run every day at 8am (0 8 * * *)

timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py signup_status_email --only-today --silent
echo "Morning signup email sent at $timestamp." >> /var/log/ion/email.log

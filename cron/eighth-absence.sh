#!/bin/bash
# run every day at 4:05pm (5 16 * * *)

timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py absence_email --silent
./cron/env.sh ./manage.py absence_notify --silent
echo "Absence email and push notification sent at $timestamp." >> /var/log/ion/email.log

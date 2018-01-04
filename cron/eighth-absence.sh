#!/bin/bash
# run every day at 4:05pm (5 16 * * *)

timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py absence_email --silent
echo "Absence email sent at $timestamp." >> /var/log/ion/email.log

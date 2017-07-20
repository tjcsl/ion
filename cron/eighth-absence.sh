#!/bin/bash
timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py absence_email --silent
echo "Absence email sent at $timestamp." >> /var/log/ion/email.log

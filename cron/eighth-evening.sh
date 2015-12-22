#!/bin/bash
timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py signup_status_email --only-tomorrow --silent
echo "Evening signup email sent at $timestamp." >> /var/log/ion/email.log
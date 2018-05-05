#!/bin/bash
# run at 10pm every day (0 22 * * *)

timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py cleartokens
echo "Expired OAuth tokens cleared at $timestamp." >> /var/log/ion/oauth-tokens.log

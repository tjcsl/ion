#!/bin/bash
# run at 8am every day (0 8 * * *)

timestamp=$(date +"%Y-%m-%d-%H%M")
cd /usr/local/www/intranet3
./cron/env.sh ./manage.py reset_routes
echo "Reset bus routes at $timestamp." >> /var/log/ion/bus.log

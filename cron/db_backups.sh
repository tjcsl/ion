#!/bin/bash
timestamp=$(date +"%Y-%m-%d-%H%M")
echo "Starting backup at /usr/local/db_backups/$timestamp.pgdump.xz at $timestamp." >> /usr/local/db_backups/backup.log
cd /usr/local/db_backups
# Keep one backup a day for everything older then a month.
find -name '*.pgdump.xz' -not -name '*-0000.pgdump.xz' -not -name "`date +%Y-%m-*.pgdump.xz`" -delete
pg_dump ion -f /usr/local/db_backups/$timestamp.pgdump
xz -9 /usr/local/db_backups/$timestamp.pgdump
timestampnow=$(date +"%Y-%m-%d-%H%M")
echo "Backup completed at /usr/local/db_backups/$timestamp.pgdump.xz at $timestampnow." >> /usr/local/db_backups/backup.log

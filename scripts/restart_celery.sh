#!/bin/bash
cd "$(dirname -- "$(readlink -f -- "$0")")/.."

logdir=/var/log/ion/celery
if [ $USER == root ]; then
    piddir=/run/ion
else
    piddir=/run/user/$(id -u)/ion
fi

mkdir -p "$piddir"
mkdir -p "$logdir"

DEBUG=TRUE,PRODUCTION=FALSE celery multi restart worker1 -A intranet -l info --pidfile="$piddir/celery-%n.pid" --logfile="$logdir/celery-%n.log" -c 16


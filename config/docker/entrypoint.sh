#!/bin/sh

if [ ! -f "config/docker/first-run.log" ]; then
    echo "# Log of first run, to run initial setup again, delete this file" > config/docker/first-run.log
    /bin/sh config/docker/initial_setup.sh 2>&1 | tee -a config/docker/first-run.log
fi

sass --watch intranet/static/css:intranet/collected_static/css &  # Automatically compile modified scss files

export PYTHONUNBUFFERED=1  # Don't buffer Django output

# Wrap the run command in a loop so that it restarts if it crashes, e.g. due to a syntax error
while true
do
    uv run manage.py run 0.0.0.0:8080  # Custom run command that skips system checks for performance
    sleep 1
done

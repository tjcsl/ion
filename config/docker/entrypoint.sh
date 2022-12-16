#!/bin/sh

if [ ! -f "config/docker/first-run.log" ]; then 
    echo "# Log of first run, to run initial setup again, delete this file" > config/docker/first-run.log
    /bin/sh config/docker/initial_setup.sh | tee -a config/docker/first-run.log
fi

python3 manage.py runserver 0.0.0.0:8080
#!/bin/bash
set -e

if ! [ -d "fixtures" ]; then
    echo "No fixtures folder found!"
    exit
fi

while getopts ":f" opt > /dev/null 2>&1; do
    case $opt in
        f)
            echo "Destroying database..."
            sudo -u postgres dropdb ion
            echo "Recreating database..."
            sudo -u postgres createdb ion
            echo "Migrating..."
            ./manage.py migrate
            ;;
    esac
done

if [ "$(whoami)" != "postgres" ]; then
    echo "Not running as postgres user, switching user..."
    sudo -u postgres bash $0
    exit
fi

FIXTURES=$(find fixtures -type f -name "*.sql")

for x in $FIXTURES; do
    psql -U postgres ion < $x > /dev/null
    echo "Imported $x"
done

redis-cli flushall

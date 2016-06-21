#!/bin/bash
set -e

if ! [ -d "fixtures" ]; then
    echo "No fixtures folder found!"
    exit
fi

TABLES=$(psql -d ion -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" -t)

for x in $TABLES; do
    if [[ $x == oauth* ]]; then continue; fi
    if [[ $x == django* ]]; then continue; fi
    if [[ $x == itemreg* ]]; then continue; fi
    if [[ $x == lostfound* ]]; then continue; fi
    if [[ $x == notifications* ]]; then continue; fi
    if [[ $x == parking* ]]; then continue; fi
    if [[ $x == signage* ]]; then continue; fi
    if [[ $x == seniors* ]]; then continue; fi
    if [[ $x == printing* ]]; then continue; fi
    if [[ $x == polls* ]]; then continue; fi
    if [[ $x == board* ]]; then continue; fi
    if [[ $x == feedback* ]]; then continue; fi
    if [[ $x == ionldap* ]]; then continue; fi
    if [[ $x == emailfwd* ]]; then continue; fi
    if [[ $x == corsheaders* ]]; then continue; fi
    if [[ $x == *historical* ]]; then continue; fi

    if [[ $x == "events_tjstaruuidmap" ]]; then continue; fi

    pg_dump -d ion -t $x -O -a --disable-triggers > fixtures/$x.sql
    echo "Exported $x"
done

if [ -c "fixtures/users_user.sql" ]; then
    # Remove all of the password hashes
    sed -i -E 's/\t\![a-zA-Z0-9]+\t/\t\!\t/g' fixtures/users_user.sql
    echo "Cleaned users_user"
fi

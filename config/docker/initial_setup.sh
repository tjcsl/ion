#!/bin/sh
set -e # exit on error

BOLD='\033[1m'
BLUE='\033[0;34m'
CLEAR='\033[0m'

echo -e "${BLUE}${BOLD}Copying over secret.py...${CLEAR}"
cp -u config/docker/secret.py intranet/settings

echo -e "${BLUE}${BOLD}Collecting static...${CLEAR}"
python3 manage.py collectstatic --noinput

echo -e "${BLUE}${BOLD}Running migrations...${CLEAR}"
python3 manage.py migrate

echo -e "${BLUE}${BOLD}Copying over scripts...${CLEAR}"
cp config/scripts/*.py .

echo -e "${BLUE}${BOLD}Generating users and teachers...${CLEAR}"
for year in "freshman" "sophomore" "junior" "senior"; do
    python3 create_users.py -t student -nw -y $year -n student student1 student2 student3 student4 student5
    python3 create_users.py -t admin -nw -y $year -n admin admin1 admin2 admin3 admin4 admin5
done
python3 create_users.py -nw -ny -t admin -n admin
python3 create_users.py -t admin -c 10
python3 create_users.py -t student -c 100
python3 create_users.py -t teacher -c 20

echo -e "${BLUE}${BOLD}Creating eighth period activities...${CLEAR}"
python3 create_activities.py -c 10
python3 create_activities.py -r freshman -c 2
python3 create_activities.py -r sophomore -c 2
python3 create_activities.py -r junior -c 2
python3 create_activities.py -r senior -c 2
python3 create_activities.py -g admin_all -c 2

echo -e "${BLUE}${BOLD}Creating eighth period blocks...${CLEAR}"
python3 create_blocks.py -l A B -c 60
python3 create_blocks.py -l A B C -i 4 -c 15

echo -e "${BLUE}${BOLD}Generating vapid keys...${CLEAR}"
python3 create_vapid_keys.py

echo -e "${BLUE}${BOLD}Cleaning up scripts...${CLEAR}"
for file in config/scripts/*.py; do
    rm "$(basename "$file")"
done

echo -e "${BLUE}${BOLD}Pulling Sports...${CLEAR}"
python3 -u manage.py import_sports $(date +%m)

echo -e "${BLUE}${BOLD}Creating CSL apps...${CLEAR}"
python3 -u manage.py dev_create_cslapps

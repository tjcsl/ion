#!/bin/sh
echo "Copying secret.py to settings..."
cp -u config/docker/secret.py intranet/settings

echo "Copying create-users.py script..."
cp config/create-users.py .

echo "Collecting static files..."
python3 -u manage.py collectstatic --noinput &

echo "Running migrations..."
python3 -u manage.py migrate &

echo "Generating development data..."

echo "Creating development users..."
python3 -u create-users.py -a admin &
python3 -u create-users.py -s student student1 student2 student3 &
python3 -u create-users.py -t teacher teacher1 teacher2 teacher3 &
echo

echo "Creating imported users..."
python3 -u manage.py import_users config/data/outputs/user_import.json &
echo

echo "Creating eighth period activities..."
python3 -u manage.py import_eighth config/data/outputs/eighth_import.json &
echo

echo "Creating CSL apps..."
python3 -u manage.py dev_create_cslapps &
echo

#!/bin/sh
echo "Copying secret.py to settings..."
cp -u config/docker/secret.py intranet/settings

echo "Copying create-users.py script..."
cp config/create-users.py .

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Running migrations..."
python3 manage.py migrate

echo "Generating development data..."

echo "Creating development users..."
echo ""
python3 create-users.py -a admin
python3 create-users.py -s student student1 student2 student3
python3 create-users.py -t teacher teacher1 teacher2 teacher3
echo ""

echo "Creating imported users..."
python3 manage.py import_users config/data/outputs/user_import.json

echo "Creating eighth period activities..."
python3 manage.py import_eighth config/data/outputs/eighth_import.json

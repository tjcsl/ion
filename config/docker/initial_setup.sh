#!/bin/sh

cp -u config/docker/secret.py intranet/settings

python3 manage.py collectstatic --noinput

python3 manage.py migrate


cp config/scripts/*.py .

for year in "freshman" "sophomore" "junior" "senior"; do
    python3 create_users.py -v -t student -y $year -n student student1 student2 student3 student4 student5
    python3 create_users.py -v -t admin -y $year -n admin admin1 admin2 admin3 admin4 admin5
done
python3 create_users.py -v -ny -t admin -n admin 
python3 create_users.py -v -t admin -c 10
python3 create_users.py -v -t student -c 100
python3 create_users.py -v -t teacher -c 20

python3 create_activities.py -v -c 10
python3 create_activities.py -v -r freshman -c 2
python3 create_activities.py -v -r sophomore -c 2
python3 create_activities.py -v -r junior -c 2
python3 create_activities.py -v -r senior -c 2
python3 create_activities.py -v -g admin_all -c 2

python3 create_blocks.py -v -l A B -c 60
python3 create_blocks.py -v -l A B C -i 4 -c 15

for file in config/scripts/*.py; do
    rm $(basename $file)
done


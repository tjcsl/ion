cp -u config/secret.py intranet/settings
python3 manage.py collectstatic --noinput 
python3 manage.py migrate 
cp config/make_admin.py . 
python3 make_admin.py 
rm make_admin.py 
python3 manage.py runserver 0.0.0.0:8080
echo "Building docs..."
excludes="intranet/urls.py intranet/settings/production.py intranet/apps/api/urls.py intranet/apps/eighth/views/api.py intranet/apps/*/migrations"
sphinx-apidoc -f -o docs/source/sourcedoc intranet $excludes
make -C docs html

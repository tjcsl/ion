echo "Building docs..."
excludes="docs/source/sourcedoc intranet intranet/urls.py intranet/settings/production.py intranet/apps/api/urls.py intranet/apps/eighth/views/api.py"
sphinx-apidoc -f -o $excludes
make -C docs html

echo "Building docs..."
sphinx-apidoc -f -o docs/source/sourcedoc intranet intranet/urls.py intranet/settings/production.py
make -C docs html

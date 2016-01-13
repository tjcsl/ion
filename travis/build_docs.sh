set -e
echo "Building docs..."
excludes="intranet/urls.py intranet/settings/secret.py intranet/settings/production.py intranet/apps/*/migrations"
sphinx-apidoc -f -o docs/source/sourcedoc intranet $excludes
sphinx-build -W -b html docs/source -d build/sphinx/doctrees build/sphinx/html

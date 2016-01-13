set -e
echo "Building docs..."
excludes="intranet/settings/secret.py intranet/settings/production.py intranet/apps/*/migrations"
sphinx-apidoc -f -o docs/sourcedoc intranet $excludes
sphinx-build -W -b html docs -d build/sphinx/doctrees build/sphinx/html

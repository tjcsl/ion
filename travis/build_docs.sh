set -e
echo "Building docs..."
excludes="intranet/urls.py intranet/settings/production.py intranet/apps/*/migrations"
sphinx-apidoc -f -o docs/source/sourcedoc intranet $excludes
sphinx-build -W docs/source -d build/sphinx/doctrees build/sphinx/html

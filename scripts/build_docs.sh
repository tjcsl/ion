set -e
echo "Building docs..."
excludes="intranet/settings/secret.py intranet/apps/*/migrations"
sphinx-apidoc -f -o build/.tmp intranet $excludes
rsync --checksum build/.tmp/*.rst docs/sourcedoc/
sphinx-build -W docs -d build/sphinx/doctrees build/sphinx/html

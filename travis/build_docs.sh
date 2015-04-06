echo "Building docs..."
excludes="intranet/apps/*/migrations"
sphinx-apidoc -f -o docs/source/sourcedoc intranet $excludes
make -C docs html

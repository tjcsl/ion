set -e
echo "Building docs..."
excludes="intranet/settings/secret.py intranet/urls.py intranet/apps/*/migrations"
sphinx-apidoc -f -o build/.tmp intranet $excludes
rsync --checksum build/.tmp/*.rst docs/sourcedoc/
sphinx-build -W docs -d build/sphinx/doctrees build/sphinx/html
if ! [ -z "`git status --porcelain`" ]; then
    echo "Modified files found, did you forget to add a file?"
    git status --porcelain
    exit 1
fi


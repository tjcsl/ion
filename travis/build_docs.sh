echo "Building docs..."
sphinx-apidoc -f -o docs/source/sourcedoc intranet
make -C docs html

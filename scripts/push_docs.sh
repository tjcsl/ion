#!/bin/bash
set -e

echo "Pushing docs to GitHub Pages"

git config --global user.email "intranet@tjhsst.edu"
git config --global user.name "GitHub Actions"

git clone --depth=50 --branch=gh-pages "https://${GH_TOKEN}@github.com/tjcsl/ion.git" gh-pages
rm -rf gh-pages/*
cd gh-pages
cp -R ../build/sphinx/html/* .
git add -A .
latest=$(git log -1 --pretty=%s|sed "s/GitHub Actions build \([0-9]\+\)/\1/")
git commit -m "GitHub Actions build $GITHUB_RUN_NUMBER"
if [ "$latest" -ge "$GITHUB_RUN_NUMBER" ]; then
  echo "Not overwriting newer docs."
else
  # This will echo the remote URL, which includes the GitHub token.
  # However, GitHub Actions will redact it automatically.
  git push origin gh-pages
  echo "Pushed docs to GitHub Pages"
fi

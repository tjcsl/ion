if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
  echo "Pushing docs to Github Pages"

  cp -R docs/build/html $HOME/html_docs
  cd $HOME
  git clone --branch=gh-pages https://${GH_TOKEN}@github.com/tjcsl/ion.git gh-pages
  rm -rf gh-pages/*
  cd gh-pages
  cp -R $HOME/html_docs/* .
  git add -A .
  git commit -m "Travis build $TRAVIS_BUILD_NUMBER"
  git push -f origin gh-pages
  push_status=$?

  if [ $push_status -ne 0 ]; then
      echo "Pushed docs to Github Pages"
  else
      echo "Failed to push docs to Github Pages"
  fi

  exit $push_status
fi

***************************
How to perform common tasks
***************************

Formatting your code
====================

You can run ``./scripts/format.sh`` to automatically format your Python code to adhere to PEP8 standards.

Updating the dev branch
=======================

- git fetch --all
- git checkout dev
- git rebase origin/master
- git push --force-with-lease

Viewing documentation locally
=============================

You can view the documentation locally by running the commands below in the virtual machine.

- ./scripts/build_docs.sh
- cd build/sphinx/html
- python -m http.server 8080

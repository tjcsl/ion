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
- git pull (note that if dev has been rebased, this may cause a conflict)
- if dev has been rebased, make *absolutely* sure that you don't have any local changes
  and run git reset --hard origin/dev this *will* destroy any local changes you have made to dev.
- git rebase origin/master
- git push --force-with-lease

Viewing documentation locally
=============================

You can view the documentation locally by running the commands below in the virtual machine.

- ./scripts/build_docs.sh
- cd build/sphinx/html
- python -m http.server 8080

# Contributing to Ion
Welcome to the [TJ CSL](https://sysadmins.tjhsst.edu) repository for Intranet 3! This document explains all you need to know about contributing to Ion.

If you are a TJHSST student, you can join the `#ion` channel on the [TJ CSL Slack workspace](https://tjcsl.slack.com) to ask questions and interact with other Ion developers.  If you are not a TJHSST student, feel free to send an email to intranet [at] tjhsst [dot] edu and we will get to you as soon as we can.


## Issues
- Please use the templates. If none of them is a perfect match, choose the closest one.

## Security Vulnerabilities & Responsible Disclosure
Please see [our security policy](SECURITY.md). Do not report security vulnerabilities in the public issue tracker.

## Pull Requests
- All PRs should target `dev`, not `master`.
- If the change is anything more than a simple typo or a fairly obvious fix, please [set up a development environment](docs/setup/vagrant.rst) and test the change there before submitting a PR.
- It is strongly recommended that you [run `flake8`, `pylint`, `isort`, `scripts/format.sh`](docs/developing/styleguide.rst#what-is-enforced-in-the-build), and [the test suite](docs/developing/testing.rst#running-tests) to ensure that the build will pass. Please also read the entire [style guide](docs/developing/styleguide.rst).
- Please read [Formatting commit messages](docs/developing/howto.rst#formatting-commit-messages).
- If your PR closes an issue, include "Closes #XXX" or similar in the messages of the commits that close each issue so the issues will be [automatically closed](https://help.github.com/en/articles/closing-issues-using-keywords) when the commits are merged into `master`.
  Note that including this text in your PR's description will have no effect because the PR will be merged into `dev`, not `master`, so GitHub does not close the issue. You must add the auto-closing keywords to the *commit* messages.
- Keep each commit/PR minimal.
- Try not to introduce bugs.
- Before you commit, make a final pass and make sure you didn't add something in for debugging and forget to take it out.
- An Ion maintainer will try to review your PR as soon as possible, but please realize that they are human and have other responsibilities.
- Do not be discouraged if the maintainers require multiple rounds of review -- we want to make Ion the best it can be, and sometimes that means multiple revisions.


Thanks for contributing!

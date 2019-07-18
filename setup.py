#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

with open("README.rst", "r") as f:
    long_description = f.read()


def get_requirements():
    with open("requirements.txt") as req, open("docs/rtd-requirements.txt", "w") as rtd_file:
        for dep in req:
            print(dep.strip(), file=rtd_file)
            yield dep.strip()


setup(
    name="Ion",
    description="The next-generation Intranet platform for TJHSST",
    long_description=long_description,
    author="The TJHSST Computer Systems Lab",
    author_email="intranet@tjhsst.edu",
    url="https://github.com/tjcsl/ion",
    version="1.0",
    test_suite="intranet.test.test_suite.run_tests",
    setup_requires=["pip>=6.0", "setuptools_git"],  # session param
    install_requires=[str(dep) for dep in get_requirements()],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Django :: 1.11",
    ],
)

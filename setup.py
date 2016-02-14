#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from pip.download import PipSession
from pip.req import parse_requirements

from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    long_description = f.read()


def get_requirements():
    for dep in parse_requirements('requirements.txt', session=PipSession()):
        # FIXME: there should really be a better way to handle this...
        if dep.markers == "python_version < '3.5'" and sys.version_info >= (3, 5):
            continue
        yield dep.req

setup(
    name="Ion",
    description="The next-generation Intranet platform for TJHSST",
    long_description=long_description,
    author="The TJHSST Computer Systems Lab",
    author_email="intranet@tjhsst.edu",
    url="https://github.com/tjcsl/ion",
    version="1.0",
    license="GPL",
    test_suite='intranet.test.test_suite.run_tests',
    setup_requires=['pip>=6.0', 'setuptools_git'],  # session param
    install_requires=[str(dep) for dep in get_requirements()],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django :: 1.9',
    ],

)

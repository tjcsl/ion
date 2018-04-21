#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    long_description = f.read()


def get_requirements():
    proc = subprocess.run(['pipenv', 'lock', '-r'], stdout=subprocess.PIPE, check=True, universal_newlines=True)
    deps = [dep.strip() for dep in proc.stdout.splitlines()]
    with open('requirements.txt', 'w') as req, open('docs/rtd-requirements.txt', 'w') as rtd_file:
        for dep in deps:
            print(dep, file=req)
            print(dep, file=rtd_file)
    return deps


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
    install_requires=get_requirements(),
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django :: 2.0',
    ])

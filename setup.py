#!/usr/bin/env python
from setuptools import setup, find_packages

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name="Ion",
    description="The next-generation Intranet platform for TJHSST",
    long_description=long_description,
    author="The TJHSST Computer Systems Lab",
    author_email="intranet@tjhsst.edu",
    url="https://github.com/tjcsl/ion",
    version="1.0",
    license="GPL",
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

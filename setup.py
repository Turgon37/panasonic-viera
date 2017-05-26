#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
from setuptools import setup, find_packages

import panasonic_viera

setup(
    name='panasonic_viera',
    version=panasonic_viera.__version__,
    packages=['panasonic_viera'],
    author="Pierre GINDRAUD",
    author_email="pgindraud@gmail.com",
    description="Library to control Panasonic Viera TVs",
    long_description=open('README.md').read(),
    include_package_data=True,
    url='https://github.com/Turgon37/panasonic-viera',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Communications"
    ]
)

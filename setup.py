#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============
udocker setup
=============
Wrapper to execute basic docker containers without using docker.
This tool is a last resort for the execution of docker containers
where docker is unavailable. It only provides a limited set of
functionalities.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))

#from udocker import __version__
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('changelog') as history_file:
    history = history_file.read()

requirements = []

setup(
    author="Jorge Gomes",
    author_email='udocker@lip.pt',
    version="1.1.3",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    description="A basic user tool to execute simple docker \
        containers in batch or interactive systems without root privileges",
    scripts=['udocker'],
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='udocker',
    name='udocker',
    packages=find_packages(),
    test_suite='tests',
    url='https://github.com/indigo-dc/udocker',
    use_2to3=True,
    zip_safe=False,
)

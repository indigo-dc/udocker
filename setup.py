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

from setuptools import setup, find_packages
from udocker import __version__

with open('README.md', 'r', encoding='utf8') as readme_file:
    README = readme_file.read()

with open('CHANGELOG.md', 'r', encoding='utf8') as history_file:
    HISTORY = history_file.read()

CONF_DIR = '/udocker/etc'
REQUIREMENTS = []
SETUP_REQUIREMENTS = ['pytest-runner', ]
TEST_REQUIREMENTS = ['pytest', ]

setup(
    author="Jorge Gomes",
    author_email='udocker@lip.pt',
    version=__version__,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System',
        'Topic :: Utilities',
    ],
    description="A basic user tool to execute simple docker \
        containers in batch or interactive systems without root privileges",
    entry_points={
        'console_scripts': ['udocker=udocker.maincmd:main'],
    },
    install_requires=REQUIREMENTS,
    license="Apache Software License 2.0",
    long_description=README + '\n\n' + HISTORY,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='Linux containers, HPC on cloud, Virtualization',
    name='udocker',
    packages=find_packages(),
    data_files=[(CONF_DIR, ['etc/udocker.conf'])],
    setup_requires=SETUP_REQUIREMENTS,
    test_suite='tests',
    tests_require=TEST_REQUIREMENTS,
    url='https://github.com/indigo-dc/udocker',
    zip_safe=False,
)

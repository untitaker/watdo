# -*- coding: utf-8 -*-
'''
    watdo
    ~~~~~

    Watdo is a simple command-line todo list manager. See the README for more
    details.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import ast
import re

from setuptools import find_packages, setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('watdo/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='watdo',
    version=version,
    author='Markus Unterwaditzer',
    author_email='markus@unterwaditzer.net',
    url='https://github.com/untitaker/watdo',
    description='Task-manager for the command line.',
    license='MIT',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests.*', 'tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': ['watdo = watdo.cli:main']
    },
    install_requires=['icalendar', 'click']
)

# -*- coding: utf-8 -*-
'''
    watdo
    ~~~~~

    Watdo is a simple command-line todo list manager. See the README for more
    details.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from setuptools import setup, find_packages

setup(
    name='watdo',
    version='0.1.2',
    author='Markus Unterwaditzer',
    author_email='markus@unterwaditzer.net',
    url='https://github.com/untitaker/watdo',
    description='Task-manager for the command line.',
    long_description=open('README.md').read(),
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['watdo = watdo.cli:main']
    },
    install_requires=['icalendar']
)

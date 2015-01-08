# -*- coding: utf-8 -*-
'''
    watdo.cli_utils
    ~~~~~~~~~

    This module contains helper functions that should be useful for arbitrary
    CLI interfaces.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import os


def parse_config_value(x):
    if x.strip().lower() in ('true', 'on', 'yes'):
        return True
    elif x.strip().lower() in ('false', 'off', 'no'):
        return False
    else:
        return x


def check_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def path(p):
    p = os.path.expanduser(p)
    p = os.path.abspath(p)
    return p

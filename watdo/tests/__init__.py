# -*- coding: utf-8 -*-
'''
    watdo.tests
    ~~~~~~~~~~~

    This module contains tests for watdo.
    This particular file contains tools for testing.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import tempfile
import shutil


class TemporaryFile(object):
    '''primitive context manager for tempfiles, not comparable with Python 3's
    version.'''
    def __init__(self):
        self.path = tempfile.mkdtemp()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        shutil.rmtree(self.path)

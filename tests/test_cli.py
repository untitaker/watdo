# -*- coding: utf-8 -*-
'''
    watdo.tests.test_cli
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import watdo.cli as cli
from watdo._compat import string_types

def test_hash_directory(tmpdir):
    haha = tmpdir.join('haha.txt')
    hash0 = cli.hash_directory(str(tmpdir))
    assert isinstance(hash0, string_types)
    haha.write('one')
    hash1 = cli.hash_directory(str(tmpdir))
    assert hash1 != hash0
    hash2 = cli.hash_directory(str(tmpdir))
    assert hash2 == hash1
    haha.write('two')
    hash3 = cli.hash_directory(str(tmpdir))
    assert hash3 != hash2

def test_hash_file(tmpdir):
    haha = tmpdir.join('haha.txt')
    haha.write('one')
    hash0 = cli.hash_file(str(haha))
    haha.write('two')
    hash1 = cli.hash_file(str(haha))
    assert hash1 != hash0

# -*- coding: utf-8 -*-
'''
    watdo.compat
    ~~~~~~~~~~~~

    :copyright: (c) 2014 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import sys

PY2 = sys.version_info < (3,)
DEFAULT_ENCODING = 'utf-8'


def to_unicode(x, encoding=DEFAULT_ENCODING):
    if not isinstance(x, text_type):
        return x.decode(encoding)
    return x


def to_bytes(x, encoding=DEFAULT_ENCODING):
    if not isinstance(x, bytes):
        return x.encode(encoding)
    return x

if PY2:
    text_type = unicode
    to_native = to_bytes
else:
    text_type = str
    to_native = to_unicode

string_types = (bytes, text_type)

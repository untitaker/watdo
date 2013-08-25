# -*- coding: utf-8 -*-
'''
    watdo.datastructures
    ~~~~~~~~~~~~~~~~~~~~

    This module provides datastructures for things that are not sufficiently
    representable with native types.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''


class EventWrapper(object):
    vcal = None  # full file content, parsed (VCALENDAR)
    main = None  # the main object (VTODO, VEVENT)
    filepath = None  # the absolute filepath

    def __init__(self, vcal=None, main=None, filepath=None):
        if (vcal is None) == (main is None):
            raise TypeError('Either vcal or main must be given')
        self.vcal = vcal
        self.main = main
        self.filepath = filepath

        if main is None:
            for component in vcal.walk():
                if component.name == 'VTODO':
                    self.main = component
                    break

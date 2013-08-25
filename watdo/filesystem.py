# -*- coding: utf-8 -*-
'''
    watdo.filesystem
    ~~~~~~~~~~~~~~~~

    This module provides helper functions for accessing watdo's storage
    backend.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''


import os
from icalendar import Calendar
from .datastructures import EventWrapper


def walk_calendar(dirpath):
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isfile(filepath):
            continue

        with open(filepath, 'rb') as f:
            vcal = Calendar.from_ical(f.read())

        event = EventWrapper(vcal=vcal, filepath=filepath)
        if event.main is not None:
            yield event


def walk_calendars(path):
    ''' walk_calendars(path) -> calendar_name, events
    events = [(filepath, event), ...]'''

    for dirname in os.listdir(path):
        dirpath = os.path.join(path, dirname)
        if os.path.isfile(dirpath):
            continue
        events = list(walk_calendar(dirpath))
        if events:
            yield dirname, events

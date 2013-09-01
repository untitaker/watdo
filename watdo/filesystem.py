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
from .datastructures import EventWrapper


def walk_calendar(dirpath, all_events):
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isfile(filepath):
            continue

        with open(filepath, 'rb') as f:
            vcal = f.read()

        event = EventWrapper(vcal=vcal, filepath=filepath)
        if event.main is not None and \
            (event.status not in ('COMPLETED', 'CANCELLED') or
             all_events):
            yield event


def walk_calendars(path, all_events):
    ''' walk_calendars(path) -> calendar_name, events
    events = [(event), ...]'''

    for dirname in os.listdir(path):
        dirpath = os.path.join(path, dirname)
        if os.path.isfile(dirpath):
            continue
        events = list(walk_calendar(dirpath, all_events))
        if events:
            yield dirname, events

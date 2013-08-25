# -*- coding: utf-8 -*-
'''
    watdo.editor
    ~~~~~~~~~~~~

    This module provides utilities for generating and parsing the markdown file
    for editor mode.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from .datastructures import EventWrapper
from .filesystem import walk_calendars
import datetime
import os

DESCRIPTION_INDENT = '    '


def change_modify_event(old_event, new_event):
    def inner():
        old_event.main.update(dict((k, v) for k, v in
                                   new_event.main.iteritems() if v))
        old_event.main.pop('last-modified', None)
        old_event.main.add('last-modified', datetime.datetime.now())

        with open(old_event.filepath, 'wb') as f:
            f.write(old_event.vcal.to_ical())
    return u'Modify event: {}'.format(old_event.main.get('summary', '')), inner


def change_add_event(event):
    '''event is actually a simple dict'''
    def inner():
        raise NotImplementedError('Adding events is not yet implemented.')
    return u'Add event: "{}"'.format(event.main.get('summary', '')), inner


def change_delete_event(event):
    def inner():
        os.remove(event.filepath)
    return u'Delete event: "{}"'.format(event.main.get('summary', '')), inner


def generate_tmpfile(f, calendars_path, description_indent=DESCRIPTION_INDENT):
    '''Given a file-like object ``f`` and a path, write todo file to ``f``,
    return a ``ids`` object'''

    calendars = walk_calendars(calendars_path)
    ids = {}
    p = lambda x=u'': f.write((x + u'\n').encode('utf-8'))

    for calendar, events in sorted(calendars, key=lambda x: x[0]):
        # sort by name
        p()
        p(u'# {}'.format(calendar))
        # sort by deadline
        events.sort(key=(lambda x:
                         x.main.get('dtend', None) or datetime.datetime.now()))
        ids.setdefault(calendar, {})

        for i, event in enumerate(events, start=1):
            ids[calendar][i] = event
            p(u'{i}.  {t}'.format(i=i, t=event.main.get('summary', '')))
            for l in event.main.get('description', '').splitlines():
                p(description_indent + l)
    return ids


def parse_tmpfile(lines, description_indent=DESCRIPTION_INDENT):
    ids = {}
    calendar_name = None
    event_id = None

    for lineno, line in enumerate(lines, start=1):
        line = line.decode('utf-8').rstrip('\n')
        if line.startswith(description_indent) or not line:
            if event_id:
                if line:
                    line = line[len(description_indent):]
                ids[calendar_name][event_id].main['description'].append(line)
        elif line.startswith(u'# '):
            calendar_name = line[2:]
            event_id = None
            ids[calendar_name] = {}
        elif calendar_name and line[0].isdigit():
            event_id, event_summary = line.split(u'.  ', 1)
            event_id = int(event_id)
            if event_id in ids[calendar_name]:
                raise RuntimeError('Line {}: This list index already has been '
                                   'used for this calendar'.format(lineno))
            ids[calendar_name][event_id] = EventWrapper(main={
                'summary': event_summary,
                'description': []
            })
        else:
            raise RuntimeError('Line {}: Not decipherable'.format(lineno))

    for events in ids.itervalues():
        for event in events.itervalues():
            event = event.main
            event['description'] = '\n'.join(event['description'])
            if not event['description']:
                del event['description']

    return ids


def diff_calendars(ids_a, ids_b):
    '''Get difference between two ``ids`` objects'''
    if set(ids_a) != set(ids_b):
        raise RuntimeError('Adding, renaming and deleting calendars is not '
                           'supported.', set(ids_a), set(ids_b))

    for calendar_name in ids_a:
        calendar_a = ids_a[calendar_name]
        calendar_b = ids_b[calendar_name]
        event_ids = set(calendar_a).union(calendar_b)

        for event_id in event_ids:
            if event_id not in calendar_a and event_id in calendar_b:
                yield 'add', calendar_name, event_id
            elif event_id in calendar_a and event_id not in calendar_b:
                yield 'del', calendar_name, event_id
            else:
                event_a = calendar_a[event_id].main
                event_b = calendar_b[event_id].main

                if event_a.get('summary', '').rstrip() != \
                   event_b.get('summary', '').rstrip() or \
                   event_a.get('description', '').rstrip() != \
                   event_b.get('description', '').rstrip():
                    yield 'mod', calendar_name, event_id


def get_changes(old_ids, new_ids):
    for method, calendar_name, event_id in diff_calendars(old_ids, new_ids):
        if method == 'mod':
            old_event = old_ids[calendar_name][event_id]
            new_event = new_ids[calendar_name][event_id]
            yield change_modify_event(old_event, new_event)
        elif method == 'add':
            new_event = new_ids[calendar_name][event_id]
            yield change_add_event(new_event)
        elif method == 'del':
            old_event = old_ids[calendar_name][event_id]
            yield change_delete_event(old_event)
        else:
            # please don't happen
            raise RuntimeError('Unknown method: {}'.format(method))

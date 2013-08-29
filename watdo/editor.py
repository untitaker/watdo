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
DATE_FORMAT = '%Y/%m/%d'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = DATE_FORMAT + ' ' + TIME_FORMAT

def _strftime(x):
    if isinstance(x, datetime.datetime):
        return x.strftime(DATETIME_FORMAT)
    elif isinstance(x, datetime.date):
        return x.strftime(DATE_FORMAT)
    elif isinstance(x, datetime.time):
        return x.strftime(TIME_FORMAT)
    else:
        raise TypeError()


def change_modify_event(old_event, new_event):
    def inner(cfg):
        old_event.update(new_event)
        old_event.bump()
        
        with open(old_event.filepath, 'wb') as f:
            f.write(old_event.vcal.to_ical())
    return u'Modify event: {}'.format(old_event.main.get('summary', '')), inner


def change_add_event(event, calendar_name):
    def inner(cfg):
        fname = event.main['uid'].split('@')[0] + u'.ics'
        fpath = os.path.join(cfg['PATH'], calendar_name, fname)
        event.filepath = fpath
        with open(event.filepath, 'wb+') as f:
            f.write(event.vcal.to_ical())

    return u'Add event: "{}"'.format(event.main.get('summary', '')), inner


def change_delete_event(event):
    def inner(cfg):
        os.remove(event.filepath)
    return u'Delete event: "{}"'.format(event.main.get('summary', '')), inner

def _by_deadline(x):
    x = x.due
    if x is None or isinstance(x, datetime.time):
        return datetime.datetime.now()
    return datetime.datetime(x.year, x.month, x.day)

def generate_tmpfile(f, calendars_path, description_indent=DESCRIPTION_INDENT):
    '''Given a file-like object ``f`` and a path, write todo file to ``f``,
    return a ``ids`` object'''

    calendars = walk_calendars(calendars_path)
    ids = {}
    p = lambda x=u'', newline=u'\n': f.write((x + newline).encode('utf-8'))

    for calendar, events in sorted(calendars, key=lambda x: x[0]):
        # sort by name
        p()
        p(u'# {}'.format(calendar))
        # sort by deadline
        events.sort(key=_by_deadline)
        ids.setdefault(calendar, {})

        for i, event in enumerate(events, start=1):
            ids[calendar][i] = event
            p(u'{i}.  {t}'.format(i=i, t=event.main.get('summary', '')), u'')
            if event.due is not None:
                p(u' [{}]'.format(_strftime(event.due)))
            else:
                p()
            for l in event.main.get('description', '').splitlines():
                p(description_indent + l)
    return ids


def parse_tmpfile(lines, description_indent=DESCRIPTION_INDENT):
    ids = {}
    calendar_name = None
    event_id = None
    descriptions = {}

    for lineno, line in enumerate(lines, start=1):
        line = line.decode('utf-8').rstrip('\n')
        if line.startswith(description_indent) or not line:
            if event_id:
                if line:
                    line = line[len(description_indent):]
                descriptions[calendar_name][event_id].append(line)
        elif line.startswith(u'# '):
            calendar_name = line[2:]
            event_id = None
            ids[calendar_name] = {}
            descriptions[calendar_name] = {}
        elif calendar_name and line[0].isdigit():
            event_id, event_summary = line.split(u'.  ', 1)
            event_id = int(event_id)
            if event_id in ids[calendar_name]:
                raise RuntimeError('Line {}: This list index already has been '
                                   'used for this calendar'.format(lineno))

            ids[calendar_name][event_id] = event = EventWrapper()
            event.summary, event.due = _extract_due_date(event_summary)
            descriptions[calendar_name][event_id] = []
        else:
            raise RuntimeError('Line {}: Not decipherable'.format(lineno))

    for calendar_name, events in descriptions.iteritems():
        for event_id, description in events.iteritems():
            ids[calendar_name][event_id].description = '\n'.join(description)

    return ids

def _extract_due_date(summary):
    if not summary.endswith(u']'):
        return summary, None
    parts = summary.split(u' [')
    if len(parts) < 2:
        return summary, None
    dt_part = parts.pop()[:-1]
    joined_parts = u' ['.join(parts)

    if u' ' in dt_part:
        return (joined_parts,
                datetime.datetime.strptime(dt_part, DATETIME_FORMAT))
    elif u'/' in dt_part:
        return (joined_parts,
                datetime.datetime.strptime(dt_part, DATE_FORMAT).date())
    elif u':' in dt_part:
        return (joined_parts,
                datetime.datetime.strptime(dt_part, TIME_FORMAT).time())
    else:
        raise RuntimeError('Invalid date or datetime. [YYYY/mm/dd], [HH:MM] and '
                           '[YYYY/mm/dd HH:MM] are allowed.')


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
                ev_a = calendar_a[event_id]
                ev_b = calendar_b[event_id]

                if ev_a != ev_b:
                    yield 'mod', calendar_name, event_id


def get_changes(old_ids, new_ids):
    for method, calendar_name, event_id in diff_calendars(old_ids, new_ids):
        if method == 'mod':
            old_event = old_ids[calendar_name][event_id]
            new_event = new_ids[calendar_name][event_id]
            yield change_modify_event(old_event, new_event)
        elif method == 'add':
            new_event = new_ids[calendar_name][event_id]
            yield change_add_event(new_event, calendar_name)
        elif method == 'del':
            old_event = old_ids[calendar_name][event_id]
            yield change_delete_event(old_event)
        else:
            # please don't happen
            raise RuntimeError('Unknown method: {}'.format(method))

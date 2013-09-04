# -*- coding: utf-8 -*-
'''
    watdo.editor
    ~~~~~~~~~~~~

    This module provides utilities for generating and parsing the markdown file
    for editor mode.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from .model import EventWrapper, ParsingError, walk_calendars
import datetime
import os

DESCRIPTION_INDENT = u'    '
FLAGS_PREFIX = u' -- '
FLAGS_DELIMITER = u'; '
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


def _by_deadline(x):
    x = x.due
    if x is None or isinstance(x, datetime.time):
        return datetime.datetime.now()
    return datetime.datetime(x.year, x.month, x.day)


def generate_tmpfile(f, cfg, calendars, description_indent=DESCRIPTION_INDENT):
    '''Given a file-like object ``f`` and a path, write todo file to ``f``,
    return a ``ids`` object'''

    ids = {}
    p = lambda x: f.write(x.encode('utf-8'))

    if cfg['SHOW_ALL_TASKS']:
        p(u'// Showing all tasks')
    else:
        p(u'// Showing pending tasks (run `watdo -a` to show all)')

    for calendar, events in sorted(calendars, key=lambda x: x[0]):
        # sort by name
        p(u'\n')
        p(u'# {}'.format(calendar))
        p(u'\n')
        # sort by deadline
        events.sort(key=_by_deadline)
        ids.setdefault(calendar, {})

        for i, event in enumerate(events, start=1):
            ids[calendar][i] = event
            flags = []
            if event.due is not None:
                flags.append(_strftime(event.due))
            if event.status:
                flags.append(event.status)

            p(u'{}.  '.format(i))
            p(event.summary)
            if flags:
                p(FLAGS_PREFIX)
                p(FLAGS_DELIMITER.join(flags))
            p(u'\n')
            for l in event.description.splitlines():
                p(description_indent + l)
                p(u'\n')
    return ids


def parse_tmpfile(lines, description_indent=DESCRIPTION_INDENT):
    ids = {}
    calendar_name = None
    event_id = None
    descriptions = {}

    for lineno, line in enumerate(lines, start=1):
        line = line.decode('utf-8').rstrip(u'\n')
        if line.startswith(u'//'):
            pass
        elif line.startswith(description_indent) or not line:
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
                raise ParsingError('Line {}: This list index already has been '
                                   'used for this calendar'.format(lineno))

            ids[calendar_name][event_id] = event = EventWrapper()
            event.summary, flags = _parse_flags(event_summary)
            event.due = _extract_due_date(flags)
            event.status = _extract_status(flags)
            if flags:
                raise ParsingError(u'Line {i}: Unknown flags: {t}'.format(i=lineno, t=flags))
            descriptions[calendar_name][event_id] = []
        else:
            raise ParsingError('Line {}: Not decipherable'.format(lineno))

    for calendar_name, events in descriptions.iteritems():
        for event_id, description in events.iteritems():
            ids[calendar_name][event_id].description = u'\n'.join(description)

    return ids


def _parse_flags(text):
    res = text.rsplit(FLAGS_PREFIX, 1)
    if len(res) < 2:
        return text, []
    summary, flags = res
    return summary, filter(bool, (x.strip() for x in flags.split(FLAGS_DELIMITER)))


def _extract_due_date(flags):
    '''Allowed values for due:
        YYYY/MM/DD
        YYYY/MM/DD HH:mm
        HH:mm
    '''
    for i, flag in enumerate(flags):
        try:
            if u' ' in flag:
                rv = datetime.datetime.strptime(flag, DATETIME_FORMAT)
            elif u'/' in flag:
                rv = datetime.datetime.strptime(flag, DATE_FORMAT).date()
            elif u':' in flag:
                rv = datetime.datetime.strptime(flag, TIME_FORMAT).time()
            else:
                raise ValueError()
        except ValueError:
            pass
        else:
            del flags[i]
            return rv
            

def _extract_status(flags):
    for i, flag in enumerate(flags):
        if flag in (u'COMPLETED', u'IN-PROCESS', u'CANCELLED', u'NEEDS-ACTION'):
            del flags[i]
            return flag

    return u''


def diff_calendars(ids_a, ids_b):
    '''Get difference between two ``ids`` objects'''
    if set(ids_a) != set(ids_b):
        raise ParsingError('Adding, renaming and deleting calendars is not '
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

def get_changes(old_ids, new_ids, cfg):
    for method, calendar_name, event_id in diff_calendars(old_ids, new_ids):
        if method == 'mod':
            old_event = old_ids[calendar_name][event_id]
            new_event = new_ids[calendar_name][event_id]

            description = u'Modify: '
            if old_event.summary == new_event.summary:
                description += new_event.summary
            else:
                description += u'{} => {}'.format(old_event.summary,
                                                 new_event.summary)

            yield description, change_modify_event(cfg, old_event, new_event)
        elif method == 'add':
            new_event = new_ids[calendar_name][event_id]
            yield (u'Add: {}'.format(new_event.summary),
                   change_add_event(cfg, new_event, calendar_name))
        elif method == 'del':
            old_event = old_ids[calendar_name][event_id]
            yield (u'Delete: {}'.format(old_event.summary),
                   change_delete_event(cfg, old_event))
        else:
            # please don't happen
            raise ParsingError('Unknown method: {}'.format(method))


def change_modify_event(cfg, old_event, new_event):
    def inner(cfg):
        old_event.update(new_event)
        old_event.bump()
        old_event.write()
    return inner


def change_add_event(cfg, event, calendar_name):
    def inner(cfg):
        fname = event.main['uid'].split('@')[0] + u'.ics'
        fpath = os.path.join(cfg['PATH'], calendar_name, fname)
        event.filepath = fpath
        with open(event.filepath, 'wb+') as f:
            f.write(event.vcal.to_ical())

    return inner


def change_delete_event(cfg, event):
    def inner(cfg):
        os.remove(event.filepath)
    return inner

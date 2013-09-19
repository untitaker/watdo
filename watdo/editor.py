# -*- coding: utf-8 -*-
'''
    watdo.editor
    ~~~~~~~~~~~~

    This module provides utilities for generating and parsing the markdown file
    for editor mode.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from .model import Task, ParsingError
import datetime
import time
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
    if isinstance(x, datetime.datetime):
        return x
    if isinstance(x, datetime.date):
        return datetime.datetime(x.year, x.month, x.day)
    dt = datetime.datetime.now()
    if isinstance(x, datetime.time):
        dt.hour = x.hour
        dt.minute = x.minute
        dt.second = x.second
        return dt
    else:
        return dt


def generate_tmpfile(f, calendars, description_indent=DESCRIPTION_INDENT,
                     all_tasks=False):
    '''Given a file-like object ``f`` and a path, write todo file to ``f``,
    return a ``ids`` object'''

    ids = {}
    p = lambda x: f.write(x.encode('utf-8'))

    if all_tasks:
        p(u'// Showing all tasks')
    else:
        p(u'// Showing pending tasks (run `watdo -a` to show all)')

    for calendar, tasks in sorted(calendars, key=lambda x: x[0]):
        # sort by name
        p(u'\n')
        p(u'# {}'.format(calendar))
        p(u'\n')
        # sort by deadline
        tasks.sort(key=_by_deadline)
        ids.setdefault(calendar, {})

        for i, task in enumerate(tasks, start=1):
            ids[calendar][i] = task
            flags = []
            if task.due is not None:
                flags.append(_strftime(task.due))
            if task.status:
                flags.append(task.status)

            p(u'{}.  '.format(i))
            p(task.summary)
            if flags:
                p(FLAGS_PREFIX)
                p(FLAGS_DELIMITER.join(flags))
            p(u'\n')
            for l in task.description.splitlines():
                p(description_indent + l)
                p(u'\n')
            p(u'\n')
    return ids


def parse_tmpfile(lines, description_indent=DESCRIPTION_INDENT):
    ids = {}
    calendar_name = None
    task_id = None
    descriptions = {}

    for lineno, line in enumerate(lines, start=1):
        line = line.decode('utf-8').rstrip(u'\n')
        if line.startswith(u'//'):
            pass
        elif line.startswith(description_indent) or not line:
            if task_id:
                if line:
                    line = line[len(description_indent):]
                descriptions[calendar_name][task_id].append(line)
        elif line.startswith(u'# '):
            calendar_name = line[2:]
            task_id = None
            ids[calendar_name] = {}
            descriptions[calendar_name] = {}
        elif calendar_name and line[0].isdigit():
            task_id, task_summary = line.split(u'.  ', 1)
            task_id = int(task_id)
            if task_id in ids[calendar_name]:
                raise ParsingError('Line {}: This list index already has been '
                                   'used for this calendar'.format(lineno))

            ids[calendar_name][task_id] = task = Task()
            task.summary, flags = _parse_flags(task_summary)
            task.due = _extract_due_date(flags)
            task.status = _extract_status(flags)
            if flags:
                raise ParsingError(u'Line {i}: Unknown flags: {t}'
                                   .format(i=lineno, t=flags))
            descriptions[calendar_name][task_id] = []
        else:
            raise ParsingError('Line {}: Not decipherable'.format(lineno))

    for calendar_name, tasks in descriptions.iteritems():
        for task_id, description in tasks.iteritems():
            ids[calendar_name][task_id].description = u'\n'.join(description)

    return ids


def _parse_flags(text):
    res = text.rsplit(FLAGS_PREFIX, 1)
    if len(res) < 2:
        return text, []
    summary, flags = res
    return summary, filter(bool, (x.strip()
                                  for x in flags.split(FLAGS_DELIMITER)))


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
        if flag in (u'COMPLETED', u'IN-PROCESS', u'CANCELLED',
                    u'NEEDS-ACTION'):
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
        task_ids = set(calendar_a).union(calendar_b)

        for task_id in task_ids:
            if task_id not in calendar_a and task_id in calendar_b:
                yield 'add', calendar_name, task_id
            elif task_id in calendar_a and task_id not in calendar_b:
                yield 'del', calendar_name, task_id
            else:
                ev_a = calendar_a[task_id]
                ev_b = calendar_b[task_id]

                if ev_a != ev_b:
                    yield 'mod', calendar_name, task_id


def get_changes(old_ids, new_ids):
    for method, calendar_name, task_id in diff_calendars(old_ids, new_ids):
        if method == 'mod':
            old_task = old_ids[calendar_name][task_id]
            new_task = new_ids[calendar_name][task_id]

            description = u'Modify: '
            if old_task.summary == new_task.summary:
                description += new_task.summary
            else:
                description += u'{} => {}'.format(old_task.summary,
                                                  new_task.summary)

            yield description, _change_modify(old_task, new_task)
        elif method == 'add':
            new_task = new_ids[calendar_name][task_id]
            yield (u'Add: {}'.format(new_task.summary),
                   _change_add(new_task, calendar_name))
        elif method == 'del':
            old_task = old_ids[calendar_name][task_id]
            yield (u'Delete: {}'.format(old_task.summary),
                   _change_delete(old_task))
        else:
            # please don't happen
            raise ParsingError('Unknown method: {}'.format(method))


def _change_modify(old_task, new_task):
    def inner(cfg):
        old_task.update(new_task)
        old_task.bump()
        old_task.write()
    return inner


def _change_add(task, calendar_name):
    def inner(cfg):
        task.write(create=True, cfg=cfg, calendar_name=calendar_name)

    return inner


def _change_delete(task):
    def inner(cfg):
        os.remove(task.filepath)
    return inner

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
import os

DESCRIPTION_INDENT = u'    '
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = DATE_FORMAT + '/' + TIME_FORMAT


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
    now = datetime.datetime.now()
    if isinstance(x, datetime.datetime):
        return x
    elif isinstance(x, datetime.date):
        return datetime.datetime(x.year, x.month, x.day)
    elif isinstance(x, datetime.time):
        return datetime.datetime(now.year, now.month, now.day,
                                 x.hour, x.minute, x.second)
    else:
        return now


def generate_tmpfile(f, tasks, header=u'// watdo', description_indent=DESCRIPTION_INDENT):
    '''Given a file-like object ``f`` and a path, write todo file to ``f``,
    return a ``ids`` object'''

    ids = {}
    p = lambda x: f.write(x.encode('utf-8'))
    p(header)
    p(u'\n')

    # sort by deadline
    for i, task in enumerate(sorted(tasks, key=_by_deadline), start=1):
        ids[i] = task

        # summary
        if task.status:
            p(u'{} '.format(_status_to_alias[unicode(task.status)]))
        if task.done_date:
            p(u'{} '.format(_strftime(task.done_date)))
        p(task.summary)

        # due
        if task.due is not None:
            p(u' due:{}'.format(_strftime(task.due)))

        # calendar
        p(u' @{}'.format(task.calendar))
        p(u' id:{}\n'.format(i))

        # description
        for l in task.description.rstrip().splitlines():
            p(description_indent + l)
            p(u'\n')
    return ids


def parse_tmpfile(lines, description_indent=DESCRIPTION_INDENT):
    ids = {}
    task_id = None
    descriptions = {}

    for lineno, line in enumerate(lines, start=1):
        try:
            line = line.decode('utf-8').rstrip(u'\n')
            if line.startswith(u'//'):
                pass
            elif line.startswith(description_indent) or not line:
                if task_id:
                    if line:
                        line = line[len(description_indent):]
                    descriptions[task_id].append(line)
            else:
                task_summary = line
                flags = task_summary.split()

                task = Task()
                task.status = _extract_status(flags)
                if task.done:
                    task.done_date = _extract_done_date(flags)
                task.due = _extract_due_date(flags)
                task.calendar = _extract_calendar(flags)
                # ids don't need to be numeric, yay ducktyping!
                task_id = _extract_id(flags) or line
                task.summary = u' '.join(flags)
                if task_id in ids:
                    raise ParsingError('This list index already has been '
                                       'used for this calendar')
                ids[task_id] = task
                descriptions[task_id] = []
        except ParsingError as e:
            raise ParsingError('Line {}: {}'.format(lineno, str(e)))

    for task_id, description in descriptions.iteritems():
        ids[task_id].description = u'\n'.join(description).rstrip()

    return ids


def _extract_date(string):
    if u'/' in string:
        return datetime.datetime.strptime(string, DATETIME_FORMAT)
    elif u'-' in string:
        return datetime.datetime.strptime(string, DATE_FORMAT).date()
    elif u':' in string:
        return datetime.datetime.strptime(string, TIME_FORMAT).time()
    else:
        raise ValueError()


def _extract_due_date(flags):
    '''Allowed values:
        due:YYYY-mm-dd
        due:YYYY-mm-dd/HH:MM
        due:HH:mm
    '''
    for i, flag in enumerate(flags):
        if flag.startswith('due:'):
            flag = flag[4:]
            try:
                rv = _extract_date(flag)
            except ValueError:
                pass
            else:
                del flags[i]
                return rv

def _extract_done_date(flags):
    try:
        x = _extract_date(flags[0])
    except ValueError:
        return None
    else:
        del flags[0]
        return x

def _compile_status_table():
    statuses = [
        (u'COMPLETED', u'x'),
        (u'IN-PROCESS', u'.'),
        (u'CANCELLED', None),
        (u'NEEDS-ACTION', u'!')
    ]
    status_to_alias = {}
    alias_to_status = {}
    for full_name, alias in statuses:
        alias_to_status[full_name] = full_name
        status_to_alias[full_name] = full_name
        if alias is not None:
            status_to_alias[full_name] = alias
            alias_to_status[alias] = full_name
    return status_to_alias, alias_to_status

_status_to_alias, _alias_to_status = _compile_status_table()
del _compile_status_table

def _extract_status(flags):
    x = _alias_to_status.get(flags[0], u'')
    if x:
        del flags[0]
    return x


def _extract_calendar(flags):
    for i, flag in enumerate(flags):
        if flag.startswith(u'@'):
            del flags[i]
            return flag[1:]
    raise ParsingError('All tasks must have a calendar set.')


def _extract_id(flags):
    for i, flag in enumerate(flags):
        if flag.startswith(u'id:'):
            del flags[i]
            return int(flag[3:])


def diff_calendars(ids_a, ids_b):
    '''Get difference between two ``ids`` objects'''
    if set(x.calendar for x in ids_a.values()) != \
            set(x.calendar for x in ids_b.values()):
        raise ParsingError('Adding, renaming and deleting calendars is not '
                           'supported.', set(ids_a), set(ids_b))

    task_ids = set(ids_a).union(ids_b)
    for task_id in task_ids:
        if task_id not in ids_a and task_id in ids_b:
            yield 'add', task_id
        elif task_id in ids_a and task_id not in ids_b:
            yield 'del', task_id
        else:
            ev_a = ids_a[task_id]
            ev_b = ids_b[task_id]

            if ev_a != ev_b:
                yield 'mod', task_id


def get_changes(old_ids, new_ids):
    for method, task_id in diff_calendars(old_ids, new_ids):
        if method == 'mod':
            old_task = old_ids[task_id]
            new_task = new_ids[task_id]

            description = u'Modify: '
            if old_task.summary == new_task.summary:
                description += new_task.summary
            else:
                description += u'{} => {}'.format(old_task.summary,
                                                  new_task.summary)

            yield description, _change_modify(old_task, new_task)
        elif method == 'add':
            new_task = new_ids[task_id]
            yield (u'Add: {}'.format(new_task.summary),
                   _change_add(new_task))
        elif method == 'del':
            old_task = old_ids[task_id]
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


def _change_add(task):
    def inner(cfg):
        task.basepath = cfg['PATH']
        task.write(create=True)

    return inner


def _change_delete(task):
    def inner(cfg):
        os.remove(task.filepath)
    return inner

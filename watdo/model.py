# -*- coding: utf-8 -*-
'''
    watdo.model
    ~~~~~~~~~~~

    This module provides datastructures to represent and helper functions to
    access data on the filesystem.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''
import datetime
import icalendar
import icalendar.tools
import os


class Task(object):
    filepath = None  # the absolute filepath
    _vcal = _main = None

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():  # meh
            setattr(self, k, v)

    @property
    def vcal(self):
        '''full file content, parsed (VCALENDAR)'''
        if self._vcal is None:
            self._vcal = dummy_vcal()
        return self._vcal

    @vcal.setter
    def vcal(self, val):
        if isinstance(val, (str, unicode)):
            val = icalendar.Calendar.from_ical(val)
        self._vcal = val

    @property
    def main(self):
        '''the main object (VTODO, VEVENT)'''
        if self._main is None:
            for component in self.vcal.walk():
                if component.name == 'VTODO':
                    self._main = component
                    break
        return self._main

    @main.setter
    def main(self, val):
        self._main = val

    def write(self):
        with open(self.filepath, 'wb') as f:
            f.write(self.vcal.to_ical())

    def update(self, other):
        self.due = other.due
        self.summary = other.summary
        self.description = other.description
        self.status = other.status

    def bump(self):
        self.main.pop('last-modified', None)
        self.main.add('last-modified', datetime.datetime.now())

    @property
    def due(self):
        dt = self.main.get('due', None)
        if dt is None:
            return None
        return dt.dt

    @due.setter
    def due(self, dt):
        self.main.pop('due', None)
        if dt is not None:
            self.main.add('due', dt)

    @property
    def summary(self):
        return self.main.get('summary', u'')

    @summary.setter
    def summary(self, val):
        self.main.pop('summary', None)
        if val:
            self.main['summary'] = val

    @property
    def done(self):
        return self.status in (u'COMPLETED', u'CANCELLED')

    @property
    def description(self):
        return self.main.get('description', u'')

    @description.setter
    def description(self, val):
        self.main.pop('description', None)
        if val:
            self.main['description'] = val

    @property
    def status(self):
        return self.main.get('status', u'')

    @status.setter
    def status(self, val):
        self.main.pop('status', None)
        if val:
            self.main['status'] = val

    def __cmp__(self, x):
        return 0 if self.__eq__(x) else -1

    def __eq__(self, other):
        return (
            isinstance(other, type(self)) and
            self.summary.rstrip(u'\n') == other.summary.rstrip(u'\n') and
            self.description.rstrip(u'\n') == other.description.rstrip(u'\n') and
            self.due == other.due and
            self.status == other.status
        )

    def __repr__(self):
        return 'watdo.model.Task({})'.format({
            'description': self.description,
            'summary': self.summary,
            'due': self.due,
            'status': self.status
        })


def dummy_vcal():
    cal = icalendar.Calendar()
    cal.add('prodid', '-//watdo//mimedir.icalendar//EN')
    cal.add('version', '2.0')

    todo = icalendar.Todo()
    todo['uid'] = icalendar.tools.UIDGenerator().uid(host_name='watdo')
    cal.add_component(todo)

    return cal


class ParsingError(ValueError):
    pass


def walk_calendar(dirpath, all_tasks):
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isfile(filepath):
            continue

        with open(filepath, 'rb') as f:
            vcal = f.read()

        task = Task(vcal=vcal, filepath=filepath)
        if task.main is not None and (not task.done or all_tasks):
            yield task


def walk_calendars(path, all_tasks):
    ''' walk_calendars(path) -> calendar_name, tasks
    tasks = [(task), ...]'''

    for dirname in os.listdir(path):
        dirpath = os.path.join(path, dirname)
        if os.path.isfile(dirpath):
            continue
        tasks = list(walk_calendar(dirpath, all_tasks))
        if tasks:
            yield dirname, tasks

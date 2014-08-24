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

from ._compat import string_types, to_unicode


class Task(object):
    #: the absolute path to the directory containing all calendars
    basepath = None

    #: the calendar name
    calendar = None

    #: the task's file name
    filename = None

    #: old locations of the task that should be removed on write
    _old_filepaths = None

    #: the vcal object from the icalendar module (exposed through self.vcal)
    _vcal = None

    #: the VTODO object inside self._vcal (exposed through self.main)
    _main = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():  # meh
            setattr(self, k, v)

    @property
    def filepath(self):
        if None in (self.basepath, self.calendar, self.filename):
            return None
        return os.path.join(self.basepath, self.calendar, self.filename)

    @filepath.setter
    def filepath(self, new):
        if self._old_filepaths is None:
            self._old_filepaths = set()
        if self.filepath is not None:
            self._old_filepaths.add(self.filepath)
        self.basepath, self.calendar, self.filename = new.rsplit(u'/', 2)

    @property
    def vcal(self):
        '''full file content, parsed (VCALENDAR)'''
        if self._vcal is None:
            self._vcal = dummy_vcal()
        return self._vcal

    @vcal.setter
    def vcal(self, val):
        if isinstance(val, string_types):
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

    def write(self, create=False):
        mode = 'wb' if not create and not self._old_filepaths else 'wb+'
        if self.filename is None:
            if not create:
                raise ValueError('Create arg must be true '
                                 'if filename is None.')
            self.random_filename()
            if self.filepath is None:
                raise ValueError('basepath and calendar must be set.')
        with open(self.filepath, mode) as f:
            f.write(self.vcal.to_ical())
        while self._old_filepaths:
            os.remove(self._old_filepaths.pop())

    def random_filename(self):
        self.filename = self.main['uid'] + u'.ics'

    def update(self, other):
        self.due = other.due
        self.summary = other.summary
        self.description = other.description
        self.status = other.status
        self.calendar = other.calendar

    def bump(self):
        self.main.pop('last-modified', None)
        self.main.add('last-modified', datetime.datetime.now())

    @property
    def due(self):
        dt = self.main.get('due', None)
        if dt is None:
            return None
        dt = dt.dt
        if isinstance(dt, datetime.datetime):
            dt = dt.replace(tzinfo=None)
        return dt

    @due.setter
    def due(self, dt):
        self.main.pop('due', None)
        if dt is not None:
            if isinstance(dt, string_types):
                dt = to_unicode(dt)
            self.main.add('due', dt)

    @property
    def summary(self):
        return self.main.get('summary', u'')

    @summary.setter
    def summary(self, val):
        self.main.pop('summary', None)
        if val:
            self.main['summary'] = to_unicode(val)

    @property
    def done(self):
        return self.status in (u'COMPLETED', u'CANCELLED')

    @property
    def done_date(self):
        dt = self.main.get('completed', None)
        if dt is None:
            return None
        return dt.dt

    @done_date.setter
    def done_date(self, dt):
        self.main.pop('completed', None)
        if dt is not None:
            if isinstance(dt, string_types):
                dt = to_unicode(dt)
            self.main.add('completed', dt)

    @property
    def description(self):
        return self.main.get('description', u'')

    @description.setter
    def description(self, val):
        self.main.pop('description', None)
        if val:
            self.main['description'] = to_unicode(val)

    @property
    def status(self):
        x = self.main.get('status', u'NEEDS-ACTION')
        return x if x != u'NEEDS-ACTION' else u''

    @status.setter
    def status(self, val):
        self.main.pop('status', None)
        if val:
            self.main['status'] = to_unicode(val)

    def __cmp__(self, x):
        return 0 if self.__eq__(x) else -1

    def __eq__(self, other):
        return all((
            isinstance(other, type(self)),
            self.summary.rstrip(u'\n') == other.summary.rstrip(u'\n'),
            self.description.rstrip(u'\n') == other.description.rstrip(u'\n'),
            self.due == other.due,
            self.status == other.status
        ))

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


def walk_calendar(dirpath):
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if not os.path.isfile(filepath):
            continue

        with open(filepath, 'rb') as f:
            vcal = f.read()

        task = Task(vcal=vcal, filepath=filepath)
        if task.main is not None:
            yield task


def walk_calendars(path):
    '''Yield name of and absolute path to each available calendar.'''
    for dirname in os.listdir(path):
        dirpath = os.path.join(path, dirname)
        if not os.path.isfile(dirpath):
            for task in walk_calendar(dirpath):
                yield task

# -*- coding: utf-8 -*-
'''
    watdo.datastructures
    ~~~~~~~~~~~~~~~~~~~~

    This module provides datastructures for things that are not sufficiently
    representable with native types.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''
import datetime
import icalendar
import icalendar.tools


class EventWrapper(object):
    vcal = None  # full file content, parsed (VCALENDAR)
    main = None  # the main object (VTODO, VEVENT)
    filepath = None  # the absolute filepath

    def __init__(self, vcal=None, main=None, filepath=None):
        if vcal is not None and main is not None:
            raise TypeError()
        if isinstance(vcal, (str, unicode)):
            vcal = icalendar.Calendar.from_ical(vcal)
        if vcal is None:
            vcal = dummy_vcal()

        if main is None:
            for component in vcal.walk():
                if component.name == 'VTODO':
                    main = component
                    break

        self.vcal = vcal
        self.main = main
        self.filepath = filepath


    def write(self):
        with open(self.filepath, 'wb') as f:
            f.write(self.vcal.to_ical())


    def update(self, other):
        self.due = other.due
        self.summary = other.summary
        self.description = other.description

    def bump(self):
        self.main.pop('last-modified', None)
        self.main.add('last-modified', datetime.datetime.now())

    @property
    def due(self):
        '''How about actual datetimes if it's called *dt*end?'''
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
        if val:
            self.main['summary'] = val
        else:
            self.main.pop('summary', None)

    @property
    def description(self):
        return self.main.get('description', u'')

    @description.setter
    def description(self, val):
        if val:
            self.main['description'] = val
        else:
            self.main.pop('description', None)

    @property
    def status(self):
        return self.main.get('status', '')

    @status.setter
    def status(self, val):
        if val:
            self.main['status'] = val
        else:
            self.main.pop('status', None)

    def __cmp__(self, x):
        return 0 if self.__eq__(x) else -1

    def __eq__(self, other):
        return isinstance(other, type(self)) and \
               self.summary.rstrip(u'\n') == other.summary.rstrip(u'\n') and \
               self.description.rstrip(u'\n') == other.description.rstrip(u'\n') and \
               self.due == other.due

    def __repr__(self):
        return 'EventWrapper({})'.format({
            'description': self.description,
            'summary': self.summary,
            'due': self.due
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

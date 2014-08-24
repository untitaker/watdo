# -*- coding: utf-8 -*-
'''
    watdo.tests.test_model
    ~~~~~

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import watdo.model as model
Task = model.Task


class TestTask(object):
    def test_writing(self, tmpdir):
        t = Task(
            summary='My little task',
            description=('This is my task\n'
                         'My task is amazing\n\n'
                         'it is t3h r0xx0rz'),
            calendar='foo_cal',
            basepath=str(tmpdir)
        )
        calendar = tmpdir.mkdir('foo_cal')
        t.write(create=True)
        assert t.filepath.startswith(str(calendar))

        with open(t.filepath, 'rb') as f:
            lines = set(map(bytes.strip, f))
            assert b'BEGIN:VCALENDAR' in lines
            assert b'VERSION:2.0' in lines
            assert b'PRODID:-//watdo//mimedir.icalendar//EN' in lines
            assert b'BEGIN:VTODO' in lines
            assert b'SUMMARY:My little task' in lines
            assert any(b'This is my task' in line for line in lines)

    def test_updating(self):
        a = Task(summary='My cool task one')
        b = Task(summary='My cool task two')
        a.update(b)
        assert a.summary == b.summary == 'My cool task two'

    def test_repr(self):
        assert 'watdo.model.Task' in repr(Task())

    def test_bump(self):
        a = Task()
        a.bump()  # last-modified doesn't exist yet
        old_date = a.main['last-modified']
        a.bump()
        assert a.main['last-modified'].dt > old_date.dt


class TestFileSystem(object):
    def test_walk_calendar(self, tmpdir):
        tasks = [
            Task(summary='task1.1', calendar='cal1'),
            Task(summary='task1.2', calendar='cal1'),
            Task(summary='task1.3', calendar='cal1'),
            Task(summary='task2.1', calendar='cal2'),
            Task(summary='task2.2', calendar='cal2'),
            Task(summary='task2.3', calendar='cal2'),
            Task(summary='task3.1', calendar='cal3'),
            Task(summary='task3.2', calendar='cal3', status='COMPLETED'),
            Task(summary='task3.3', calendar='cal3')
        ]

        calendars = set()

        for task in tasks:
            if task.calendar not in calendars:
                tmpdir.mkdir(task.calendar)
                calendars.add(task.calendar)
            task.basepath = str(tmpdir)
            task.write(create=True)

        rv = sorted(model.walk_calendars(str(tmpdir)),
                    key=lambda x: x.summary)

        assert tasks == rv

# -*- coding: utf-8 -*-
'''
    watdo.tests.test_model
    ~~~~~

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from watdo.tests import TestCase, TemporaryFile
import watdo.model as model
Task = model.Task
import os


class TaskTestCase(TestCase):
    def test_writing(self):
        with TemporaryFile() as tmp:
            t = Task(
                summary='My little task',
                description=('This is my task\n'
                             'My task is amazing\n\n'
                             'it is t3h r0xx0rz'),
                calendar='foo_cal',
                basepath=tmp.path
            )
            os.mkdir(os.path.join(tmp.path, 'foo_cal'))
            t.write(create=True)
            assert t.filepath.startswith(os.path.join(tmp.path, 'foo_cal'))
            with open(t.filepath) as f:
                lines = set(map(str.strip, f))
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


class FileSystemTestCase(TestCase):
    def test_walk_calendar(self):
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

        with TemporaryFile() as tmp:
            for task in tasks:
                dirpath = os.path.join(tmp.path, task.calendar)
                if not os.path.isdir(dirpath):
                    os.mkdir(dirpath)
                task.basepath = tmp.path
                task.write(create=True)

            rv = sorted(model.walk_calendars(tmp.path, all_tasks=True),
                        key=lambda x: x.summary)
            assert tasks == rv

            rv = sorted(model.walk_calendars(tmp.path, all_tasks=False),
                        key=lambda x: x.summary)
            del tasks[-2]
            assert tasks == rv

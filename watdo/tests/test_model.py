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
        t = Task(
            summary='My little task',
            description=('This is my task\n'
                         'My task is amazing\n\n'
                         'it is t3h r0xx0rz')
        )
        with TemporaryFile() as tmp:
            os.mkdir(os.path.join(tmp.path, 'foo_cal'))
            t.write(create=True, cfg={'PATH': tmp.path},
                    calendar_name='foo_cal')
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


def FileSystemTestCase(TestCase):
    def test_walk_calendar(self):
        tasks = lambda *l: [Task(summary=x) for x in l]
        calendars = [
            ('cal1', tasks('task1.1', 'task1.2', 'task1.3')),
            ('cal2', tasks('task2.1', 'task2.2', 'task2.3')),
            ('cal3', tasks('task3.1', 'task3.2', 'task3.3'))
        ]
        # task 3.2
        calendars[-1][1][1].status = 'COMPLETED'

        with TemporaryFile() as tmp:
            for name, tasks in calendars:
                os.mkdir(os.path.join(tmp.path, name))
                for task in tasks:
                    task.write(create=True, cfg={'PATH': tmp.path},
                               calendar_name=name)

            rv = [(name, list(tasks)) for name, tasks in
                  model.walk_calendars(tmp.path, all_tasks=True)]
            assert calendars == rv

            rv = [(name, list(tasks)) for name, tasks in
                  model.walk_calendars(tmp.path, all_tasks=False)]
            del calendars[-1][1][1]
            assert calendars == rv

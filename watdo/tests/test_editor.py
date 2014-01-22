# -*- coding: utf-8 -*-
'''
    watdo.tests.test_editor
    ~~~~~

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

from watdo.tests import TestCase, StringIO
from watdo.model import Task, ParsingError
import watdo.editor as editor
import datetime


class EditorTestCase(TestCase):
    def test_basic(self):
        f = StringIO()
        tasks = [
            Task(summary=u'My cool task 1', description=u'lel', calendar='test_cal'),
            Task(summary=u'My cool task 2', calendar='test_cal')
        ]
        old_ids = editor.generate_tmpfile(f, tasks)

        lines = f.getvalue().splitlines()

        assert lines[1:] == [
            'My cool task 1 @test_cal id:1',
            '    lel',
            'My cool task 2 @test_cal id:2'
        ]

        lines[-1] = 'My cool modified task 2 @test_cal id:2'
        new_ids = editor.parse_tmpfile(lines)
        ids_diff = editor.diff_calendars(old_ids, new_ids)
        assert set(ids_diff) == set([
            ('mod', 2)
        ])

        del lines[:-1]
        lines.append('')  # it has to take that
        lines.append('')
        new_ids = editor.parse_tmpfile(lines)
        ids_diff = editor.diff_calendars(old_ids, new_ids)

        assert set(ids_diff) == set([
            ('del', 1),
            ('mod', 2)
        ])

    def test_date_and_time(self):
        for due, formatted_due, new_due, formatted_new_due in [
            (datetime.date(2013, 9, 11), '2013/09/11',
             datetime.date(2013, 12, 17), '2013/12/17'),
            (datetime.time(13, 37), '13:37',
             datetime.time(14, 40), '14:40'),
            (datetime.datetime(2013, 9, 11, 13, 37), '2013/09/11-13:37',
             datetime.datetime(2013, 12, 17, 14, 40), '2013/12/17-14:40')
        ]:

            f = StringIO()
            task = Task(summary=u'My cool task', due=due, calendar='test_cal')
            tasks = [task]
            old_ids = editor.generate_tmpfile(f, tasks)
            lines = f.getvalue().splitlines()

            assert lines[1] == 'My cool task due:{} @test_cal id:1'.format(formatted_due)

            lines[1] = 'My cool task @test_cal due:{} id:1'.format(formatted_new_due)
            new_ids = editor.parse_tmpfile(lines)
            ids_diff = editor.diff_calendars(old_ids, new_ids)

            assert set(ids_diff) == set([
                ('mod', 1)
            ])
            assert new_ids[1].due == new_due

    def test_task_id_twice(self):
        with self.assertRaisesRegexp(ParsingError,
                                     'index already has been used'):
            editor.parse_tmpfile([
                'cool task 1 @test_cal id:1',
                'cool task 2 @test_cal id:2',
                'cool task 3 @test_cal id:1'
            ])

    def test_missing_calendar(self):
        with self.assertRaises(ParsingError):
            editor.parse_tmpfile(['ASDASDASDASDAD'])

    def test_descriptions(self):
        calendars = [
            Task(
                summary='Hello World',
                description='This is a test\nIt has multiple linez\n',
                calendar='test_cal'
            )
        ]

        f = StringIO()
        old_ids = editor.generate_tmpfile(f, calendars)

        new_ids = editor.parse_tmpfile(f.getvalue().splitlines())
        assert old_ids == new_ids

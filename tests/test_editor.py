# -*- coding: utf-8 -*-
'''
    watdo.tests.test_editor
    ~~~~~

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import datetime

import pytest

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

from watdo._compat import to_bytes
import watdo.editor as editor
from watdo.model import ParsingError, Task


def test_basic():
    f = BytesIO()
    tasks = [
        Task(summary=u'My cool task 1', description=u'lel',
             calendar='test_cal'),
        Task(summary=u'My cool task 2', calendar='test_cal')
    ]
    old_ids = editor.generate_tmpfile(f, tasks)

    lines = f.getvalue().splitlines()

    assert lines[1:] == [
        b'My cool task 1 @test_cal id:1',
        b'    lel',
        b'My cool task 2 @test_cal id:2'
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


def test_date_and_time():
    for due, formatted_due, new_due, formatted_new_due in [
        (datetime.date(2013, 9, 11), '2013-09-11',
         datetime.date(2013, 12, 17), '2013-12-17'),
        (datetime.time(13, 37), '13:37',
         datetime.time(14, 40), '14:40'),
        (datetime.datetime(2013, 9, 11, 13, 37), '2013-09-11/13:37',
         datetime.datetime(2013, 12, 17, 14, 40), '2013-12-17/14:40')
    ]:

        f = BytesIO()
        task = Task(summary=u'My cool task', due=due, calendar='test_cal')
        tasks = [task]
        old_ids = editor.generate_tmpfile(f, tasks)
        lines = f.getvalue().splitlines()

        assert lines[1] == to_bytes(u'My cool task due:{} @test_cal id:1'
                                    .format(formatted_due))

        lines[1] = to_bytes('My cool task @test_cal due:{} id:1'
                            .format(formatted_new_due))
        new_ids = editor.parse_tmpfile(lines)
        ids_diff = editor.diff_calendars(old_ids, new_ids)

        assert set(ids_diff) == set([
            ('mod', 1)
        ])
        assert new_ids[1].due == new_due


def test_task_id_twice():
    with pytest.raises(ParsingError) as excinfo:
        editor.parse_tmpfile([
            'cool task 1 @test_cal id:1',
            'cool task 2 @test_cal id:2',
            'cool task 3 @test_cal id:1'
        ])

    assert 'index already has been used' in str(excinfo.value)


def test_missing_calendar():
    with pytest.raises(ParsingError):
        editor.parse_tmpfile(['ASDASDASDASDAD'])


def test_descriptions():
    calendars = [
        Task(
            summary='Hello World',
            description='This is a test\nIt has multiple linez\n',
            calendar='test_cal'
        )
    ]

    f = BytesIO()
    old_ids = editor.generate_tmpfile(f, calendars)

    new_ids = editor.parse_tmpfile(f.getvalue().splitlines())
    assert old_ids == new_ids

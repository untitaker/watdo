from watdo.tests import TestCase, StringIO
from watdo.model import Task, ParsingError
import watdo.editor as editor
import datetime


class EditorTestCase(TestCase):
    def test_basic(self):
        f = StringIO()
        calendars = [
            ('test_cal', [
                Task(summary=u'My cool task 1'),
                Task(summary=u'My cool task 2')
            ])
        ]
        old_ids = editor.generate_tmpfile(f, calendars)

        lines = f.getvalue().splitlines()

        assert lines[0].startswith('// Showing pending tasks')
        assert lines[1:] == [
            '# test_cal',
            '1.  My cool task 1',
            '2.  My cool task 2'
        ]

        lines[-1] = '2.  My cool modified task 2'
        new_ids = editor.parse_tmpfile(lines)

        ids_diff = editor.diff_calendars(old_ids, new_ids)
        assert set(ids_diff) == set([
            ('mod', 'test_cal', 2)
        ])

        del lines[-2]
        lines.append('')  # it has to take that
        lines.append('')
        new_ids = editor.parse_tmpfile(lines)
        ids_diff = editor.diff_calendars(old_ids, new_ids)

        assert set(ids_diff) == set([
            ('del', 'test_cal', 1),
            ('mod', 'test_cal', 2)
        ])

    def test_date_and_time(self):
        for due, formatted_due, new_due, formatted_new_due in [
            (datetime.date(2013, 9, 11), '2013/09/11',
             datetime.date(2013, 12, 17), '2013/12/17'),
            (datetime.time(13, 37), '13:37',
             datetime.time(14, 40), '14:40'),
            (datetime.datetime(2013, 9, 11, 13, 37), '2013/09/11 13:37',
             datetime.datetime(2013, 12, 17, 14, 40), '2013/12/17 14:40')
        ]:

            f = StringIO()
            task = Task(summary=u'My cool task', due=due)
            calendars = [('test_cal', [task])]
            old_ids = editor.generate_tmpfile(f, calendars, all_tasks=False)
            lines = f.getvalue().splitlines()

            assert lines[2] == '1.  My cool task -- ' + formatted_due

            lines[2] = '1.  My cool task -- ' + formatted_new_due
            new_ids = editor.parse_tmpfile(lines)
            ids_diff = editor.diff_calendars(old_ids, new_ids)

            assert set(ids_diff) == set([
                ('mod', 'test_cal', 1)
            ])
            assert new_ids['test_cal'][1].due == new_due

    def test_task_id_twice(self):
        with self.assertRaisesRegexp(ParsingError,
                                     'index already has been used'):
            editor.parse_tmpfile([
                '# test_cal',
                '1.  cool task 1',
                '2.  cool task 2',
                '1.  cool task 3'
            ])

    def test_unknown_flags(self):
        with self.assertRaisesRegexp(ParsingError, 'Line 3: Unknown flags'):
            editor.parse_tmpfile([
                '# test_cal',
                '1.  cool task 1 -- COMPLETED',
                '2.  cool task 2 -- HEYHOO'
            ])

    def test_complete_bogus(self):
        with self.assertRaises(ParsingError):
            editor.parse_tmpfile(['ASDASDASDASDAD'])

    def test_descriptions(self):
        calendars = [
            ('test_cal', [
                Task(
                    summary='Hello World',
                    description='This is a test\nIt has multiple linez\n'
                )
            ])
        ]

        f = StringIO()
        old_ids = editor.generate_tmpfile(f, calendars)

        new_ids = editor.parse_tmpfile(f.getvalue().splitlines())
        assert old_ids == new_ids

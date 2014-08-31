# -*- coding: utf-8 -*-
'''
    watdo.tests.test_cli
    ~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''

import time

from click.testing import CliRunner

import watdo.cli as cli
from watdo._compat import string_types

def test_basic_run(tmpdir):
    tasks_dir = tmpdir.mkdir('tasks')
    default_cal = tasks_dir.mkdir('default')
    tmp_dir = tmpdir.mkdir('tmp')
    config = tmpdir.join('config')
    config.write(
        '[watdo]\n'
        'confirmation = False\n'
        'path = {path}\n'
        'tmppath = {tmppath}'.format(
            path=str(tasks_dir),
            tmppath=str(tmp_dir)
        )
    )

    runner = CliRunner()
    result = runner.invoke(cli.main, env={
        'WATDO_CONFIG': str(config),
        'EDITOR': 'echo "My cool task @default" >> '
    }, catch_exceptions=False)
    assert not result.exception

    task, = default_cal.listdir()
    assert 'My cool task' in task.read()

    result = runner.invoke(cli.main, env={
        'WATDO_CONFIG': str(config),
        'EDITOR': 'echo "Invalid task @wrongcalendar" >> '
    }, catch_exceptions=False, input='n\n')
    assert result.exception
    assert ('Calendars are not explicitly created. '
            'Please create the directory {} yourself.'
            .format(str(tasks_dir.join('wrongcalendar')))) \
            in result.output.splitlines()

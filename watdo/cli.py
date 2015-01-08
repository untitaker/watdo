# -*- coding: utf-8 -*-
'''
    watdo.cli
    ~~~~~~~~~

    This module contains both helper functions and main() for the CLI
    interface.

    :copyright: (c) 2013 Markus Unterwaditzer
    :license: MIT, see LICENSE for more details.
'''


import watdo.editor as editor
import watdo.model as model
from .cli_utils import path, parse_config_value
from .exceptions import CliError
from ._compat import to_unicode
import subprocess
import functools
import tempfile
import os
import sys
import click

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser


def confirm_changes(changes):
    changes = list(changes)
    if changes:
        for i, (description, func) in enumerate(changes):
            print(u'{}.  {}'.format(i, description))

        print('List the changes you don\'t want to happen.')
        print('Just hit enter if changes are okay.')
        reverted = None
        while reverted is None:
            try:
                reverted = [int(x.strip()) for x in raw_input('> ').split()]
            except ValueError:
                print('Invalid input.')
                print('If you want to undo number 1 and 2, enter: 1 2')
        for i in reverted:
            del changes[i]
    return changes


def make_changes(changes, cfg):
    changes = list(changes)
    if not changes:
        print('Nothing to do.')
    for description, func in changes:
        print(description)
        func(cfg)


def launch_editor(cfg, all_tasks=False, calendar=None):
    tmpfile = tempfile.NamedTemporaryFile(dir=cfg['tmppath'], delete=False)

    try:
        with tmpfile as f:
            tasks = model.walk_calendars(cfg['path'])

            def task_filter():
                for task in tasks:
                    if calendar is not None and task.calendar != calendar:
                        continue
                    if not all_tasks and task.done:
                        continue
                    yield task

            header = u'// Showing {status} tasks from {calendar}'.format(
                status=(u'all' if all_tasks else u'pending'),
                calendar=(u'all calendars' if calendar is None else u'@{}'
                          .format(calendar))
            )
            old_ids = editor.generate_tmpfile(f, task_filter(), header)

        new_ids = None
        while new_ids is None:
            cmd = cfg['editor'] + ' ' + tmpfile.name
            print('>>> {}'.format(cmd))
            subprocess.call(cmd, shell=True)

            with open(tmpfile.name, 'rb') as f:
                try:
                    new_ids = editor.parse_tmpfile(f)

                    changes = editor.get_changes(old_ids, new_ids)

                    if cfg['confirmation']:
                        changes = confirm_changes(changes)
                    make_changes(changes, cfg)

                except (ValueError, CliError) as e:
                    print(e)
                    click.confirm('Do you want to edit again? '
                                  'Otherwise changes will be discarded.',
                                  default=True, abort=True)
                else:
                    break
    finally:
        os.remove(tmpfile.name)


def get_config_parser(env):
    fname = env.get('WATDO_CONFIG', path('~/.watdo/config'))
    parser = SafeConfigParser()
    parser.add_section('watdo')
    if not os.path.exists(fname):
        raise CliError('Config file {} doesn\'t exist. Please create it or '
                       'use the WATDO_CONFIG environment variable to point '
                       'watdo to a different location.'.format(fname))

    parser.read(fname)
    return dict(parser.items('watdo'))


def catch_errors(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except CliError as e:
            print(str(e))
            sys.exit(1)
    return inner


def _get_cli():
    @click.group(invoke_without_command=True)
    @click.option('--confirm/--no-confirm', default=None,
                  help=('Confirm changes. Can be set with a "confirmation" '
                        'parameter in the config file.'))
    @click.option('--all/--pending', '-a',
                  help='Show all tasks, not only unfinished ones.')
    @click.option('--calendar', '-c', help='The calendar to show')
    @click.pass_context
    @catch_errors
    def cli(ctx, confirm, all, calendar):
        if ctx.obj is None:
            ctx.obj = {}

        def bail_out(msg):
            click.echo(msg)
            ctx.abort()

        file_cfg = get_config_parser(os.environ)

        ctx.obj['path'] = path(os.environ.get('WATDO_PATH') or
                               file_cfg.get('path') or
                               '~/.watdo/tasks/')

        ctx.obj['tmppath'] = path(os.environ.get('WATDO_TMPPATH') or
                                  file_cfg.get('tmppath') or
                                  '~/.watdo/tmp/')

        ctx.obj['editor'] = (os.environ.get('WATDO_EDITOR') or
                             file_cfg.get('editor') or
                             os.environ.get('EDITOR') or
                             bail_out('No editor could be determined. Make '
                                      'sure you\'ve got either $WATDO_EDITOR '
                                      'or $EDITOR set.'))

        confirm_default = parse_config_value(
            file_cfg.get('confirmation', 'true'))

        if confirm is None:
            confirm = confirm_default

        ctx.obj['confirmation'] = confirm
        ctx.obj['show_all_tasks'] = all

        if not ctx.invoked_subcommand:
            launch_editor(
                ctx.obj,
                all_tasks=ctx.obj.get('show_all_tasks', False),
                calendar=calendar or None
            )

    @cli.command()
    @click.argument('summary')
    @click.option('--description', default='', help='An optional description.')
    @click.pass_context
    @catch_errors
    def new(ctx, summary, description):
        '''Create a new task. The summary has the same format as the first
        lines of a task inside the editor.'''
        # Not sure what the appropriate encoding is, but it probably is utf-8
        # in most cases.
        _, t = editor.parse_summary_header(to_unicode(summary, 'utf-8'))
        t.description = description
        t.basepath = ctx.obj['path']
        print(u'Creating task: "{}" in {}'.format(t.summary, t.calendar))
        t.write(create=True)

    return cli

main = _get_cli()

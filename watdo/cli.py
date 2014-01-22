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
from watdo.cli_utils import path, confirm, check_directory, bail_out
import subprocess
import tempfile
import os
import sys
import argparse
import ConfigParser


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


def launch_editor(cfg, tmpfilesuffix='.markdown', all_tasks=False, calendar=None):
    tmpfile = tempfile.NamedTemporaryFile(dir=cfg['TMPPATH'],
                                          suffix=tmpfilesuffix, delete=False)

    try:
        with tmpfile as f:
            tasks = model.walk_calendars(cfg['PATH'])

            def task_filter():
                for task in tasks:
                    if calendar is not None and task.calendar != calendar:
                        continue
                    if not all_tasks and task.done:
                        continue
                    yield task

            header = u'// Showing {status} tasks from {calendar}'.format(
                status=(u'all' if all_tasks else u'pending'),
                calendar=(u'all calendars' if calendar is None else u'@{}'.format(calendar))
            )
            old_ids = editor.generate_tmpfile(f, task_filter(), header)

        new_ids = None
        while new_ids is None:
            cmd = cfg['EDITOR'] + ' ' + tmpfile.name
            print('>>> {}'.format(cmd))
            subprocess.call(cmd, shell=True)

            with open(tmpfile.name, 'rb') as f:
                try:
                    new_ids = editor.parse_tmpfile(f)
                except ValueError as e:
                    print(e)
                    print('Press enter to edit again...')
                    raw_input()

        return editor.get_changes(old_ids, new_ids)
    finally:
        os.remove(tmpfile.name)


def get_argument_parser():
    epilog = '''
Common operations:
watdo  # show pending tasks from all calendars
watdo -a  # show all tasks, even finished ones
watdo computers  # show pending tasks from calendar "computers"
watdo computers -n "remove virus"  # add task to "computers"
echo "HDD wipe neccessary" | watdo computers -n "remove virus"  # add task with description
'''
    parser = argparse.ArgumentParser(
        description='Simple task-list manager.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog)
    parser.add_argument('--all', '-a', dest='show_all_tasks',
                        action='store_const', const=True, default=None,
                        help=('Watdo normally shows only uncompleted tasks '
                              'and marks them as done if they get deleted '
                              'from the tmpfile. This mode will make watdo '
                              'show all tasks and actually delete them.'))
    parser.add_argument('--new', '-n', dest='new_task', default=None,
                        help='Create new task instead of opening the editor. '
                        'Needs a calendar to add the task to, and takes a '
                        'description through stdin.')
    parser.add_argument('calendar_name', nargs='?', default=None,
                        help='Optional, a calendar to operate on.')
    parser.add_argument('--noconfirm', dest='confirmation',
                        action='store_const', const=False, default=None,
                        help=('Disable any confirmations.'))

    return parser


def create_config_file():
    def input(msg):
        return raw_input(msg + ' ').strip() or None
    cfg = {
        'editor': input('Your favorite editor? [default: $EDITOR]'),
        'path': input('Where are your tasks stored? '
                      '[default: ~/.watdo/tasks/]'),
        'tmppath': input('Where should tmpfiles for editing be stored? '
                         '[default: ~/.watdo/tmp/]')
    }
    return ((k, v) for k, v in cfg.iteritems() if v)


def get_config_parser(env):
    fname = env.get('WATDO_CONFIG', path('~/.watdo/config'))
    parser = ConfigParser.SafeConfigParser()
    parser.add_section('watdo')
    if not os.path.exists(fname) and \
       confirm('Config file {} doesn\'t exist. '
               'Create? (Y/n)'.format(fname)):
        check_directory(os.path.dirname(fname))
        for k, v in create_config_file():
            parser.set('watdo', k, v)
        with open(fname, 'wb+') as f:
            parser.write(f)

    parser.read(fname)
    return dict(parser.items('watdo'))


def main():
    env = os.environ
    args = vars(get_argument_parser().parse_args())
    cfg = get_config_parser(os.environ)
    _main(env, args, cfg)


def _main(env, args, file_cfg):
    cfg = {
        'PATH': path(
            env.get('WATDO_PATH') or
            file_cfg.get('path') or
            '~/.watdo/tasks/'
        ),
        'TMPPATH': path(
            env.get('WATDO_TMPPATH') or
            file_cfg.get('tmppath') or
            '~/.watdo/tmp/'
        ),
        'EDITOR': (
            env.get('WATDO_EDITOR') or
            file_cfg.get('editor') or
            env.get('EDITOR') or
            bail_out('No editor could be determined. Make sure you\'ve got '
                     'either $WATDO_EDITOR or $EDITOR set.')
        ),
        'CONFIRMATION': next((x for x in (args['confirmation'], True)
                              if x is not None))
    }

    if args['new_task'] is not None:
        # create a new task
        calendar, summary = args['calendar_name'], args['new_task']
        if not summary:
            bail_out('Missing summary.')
        if not calendar:
            bail_out('Missing calendar.')
        if sys.stdin.isatty():
            print('I see you haven\'t piped anything into watdo for the \n'
                  'description. Type something and hit ^D if you\'re done.')
        description = sys.stdin.read()
        t = model.Task(summary=summary, description=description)
        t.basepath = cfg['PATH']
        t.calendar = calendar
        print('Creating task: "{}" in {}'.format(summary, calendar))
        t.write(create=True)

    else:
        # display all tasks from calendar, default to all calendars
        changes = launch_editor(cfg, all_tasks=args['show_all_tasks'], calendar=args['calendar_name'])
        if cfg['CONFIRMATION']:
            changes = confirm_changes(changes)
        make_changes(changes, cfg)

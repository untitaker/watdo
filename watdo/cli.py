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
import subprocess
import tempfile
import os
import sys
import argparse
import ConfigParser


def bail_out(msg):
    print(msg)
    sys.exit(1)


def check_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def confirm_changes(changes):
    changes = list(changes)
    if changes:
        for i, (description, func) in enumerate(changes):
            print(u'{}.  {}'.format(i, description))

        print('Enter changes you don\'t want to happen.')
        print('By number, space separated.')
        reverted = raw_input('> ')
        for i in (int(x.strip()) for x in reverted.split()):
            del changes[i]
    return changes


def make_changes(changes, cfg):
    changes = list(changes)
    if not changes:
        print('Nothing to do.')
    for description, func in changes:
        print(description)
        func(cfg)


def path(p):
    p = os.path.expanduser(p)
    p = os.path.abspath(p)
    return p


def confirm(message='Are you sure? (Y/n)'):
    inp = raw_input(message).lower().strip()
    if not inp or inp == 'y':
        return True
    return False


def launch_editor(cfg, tmpfilesuffix='.markdown', all_tasks=False):
    tmpfile = tempfile.NamedTemporaryFile(dir=cfg['TMPPATH'],
                                          suffix=tmpfilesuffix, delete=False)

    try:
        with tmpfile as f:
            calendars = model.walk_calendars(cfg['PATH'], all_tasks=all_tasks)
            old_ids = editor.generate_tmpfile(f, calendars)

        new_ids = None
        while new_ids is None:
            cmd = [cfg['EDITOR'], tmpfile.name]
            print('>>> ' + ' '.join(cmd))
            subprocess.call(cmd)

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
    parser = argparse.ArgumentParser(description='Simple task-list manager.')
    parser.add_argument('--all', '-a', dest='show_all_tasks',
                        action='store_const', const=True, default=None,
                        help=('Watdo normally shows only uncompleted tasks '
                              'and marks them as done if they get deleted '
                              'from the tmpfile. This mode will make watdo '
                              'show all tasks and actually delete them.'))
    parser.add_argument('--new', '-n', dest='new_task', default=None,
                        help='Create a new task instead of opening the editor. '
                        'Needs --cal defined, and takes a summary through '
                        'stdin.')
    parser.add_argument('--cal', '-c', dest='calendar_name', default=None,
                        help='A calendar name. Exact meaning depends on other '
                        'arguments.')
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


def first(*a):
    '''Used instead of the `or` operator if a *has* to be None in order to
    evaluate to b, useful for cli flags where the values may be True, False or
    None.

    Otherwise just use `a or b`
    '''
    for x in a:
        if x is not None:
            return x


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
        'CONFIRMATION': first(args['confirmation'], True)
    }

    if args['new_task'] is not None:
        # watdo -n "my task" -c my_calendar
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
        print('Creating task: "{}" in {}'.format(summary, calendar))
        t.write(create=True, cfg=cfg, calendar_name=calendar)

    else:
        # watdo
        changes = launch_editor(cfg, all_tasks=args['show_all_tasks'])
        if cfg['CONFIRMATION']:
            changes = confirm_changes(changes)
        make_changes(changes, cfg)

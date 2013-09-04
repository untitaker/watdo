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
import subprocess
import os
import argparse


def check_directory(path):
    if not os.path.exists(path):
        if confirm(u'Directory {} doesn\'t exist. Create? (Y/n)'.format(path)):
            os.makedirs(path)
        else:
            raise RuntimeError(u'Directory {} doesn\'t exist.'.format(path))


def confirm_changes(changes):
    changes = list(changes)
    if not changes:
        print('No changes.')
    else:
        for i, (description, func) in enumerate(changes):
            print(u'{}.  {}'.format(i, description))

        print('Enter changes you don\'t want to happen.')
        print('By number, space separated.')
        reverted = raw_input('> ')
        for i in (int(x.strip()) for x in reverted.split()):
            del changes[i]

    return changes


def confirm(message='Are you sure? (Y/n)'):
    inp = raw_input(message).lower().strip()
    if not inp or inp == 'y':
        return True
    return False


def launch_editor(cfg, tmpfilename='todo.markdown'):
    tmpfilepath = os.path.join(cfg['TMPPATH'], tmpfilename)

    with open(tmpfilepath, 'wb+') as f:
        old_ids = editor.generate_tmpfile(f, cfg,
            editor.walk_calendars(
                cfg['PATH'],
                all_events=cfg['SHOW_ALL_TASKS']
            )
        )

    new_ids = None
    while new_ids is None:
        cmd = [cfg['EDITOR'], tmpfilepath]
        print('>>> ' + ' '.join(cmd))
        subprocess.call(cmd)

        with open(tmpfilepath, 'rb') as f:
            try:
                new_ids = editor.parse_tmpfile(f)
            except ValueError as e:
                print(e)
                print('Press enter to edit again...')
                raw_input()

    changes = confirm_changes(editor.get_changes(old_ids, new_ids, cfg))
    for description, func in changes:
        print(description)
        func(cfg)

    os.remove(tmpfilepath)


def get_argument_parser():
    parser = argparse.ArgumentParser(description='Simple task-list manager.')
    parser.add_argument('--all', '-a', dest='show_all_tasks',
                        action='store_const', const=True, default=None,
                        help=('Watdo normally shows only uncompleted tasks '
                              'and marks them as done if they get deleted '
                              'from the tmpfile. This mode will make watdo '
                              'show all tasks and actually delete them.'))
    return parser


def _main(env, args):
    pjoin = os.path.join
    abspath = os.path.abspath
    cfg = {
        'PATH': abspath(env.get('WATDO_PATH')
                        or pjoin(env['HOME'], '.watdo/tasks/')),
        'TMPPATH': abspath(env.get('WATDO_TMPPATH')
                           or pjoin(env['HOME'], '.watdo/tmp/')),
        'EDITOR': env.get('WATDO_EDITOR') or env.get('EDITOR') or None
    }

    cfg['SHOW_ALL_TASKS'] = args['show_all_tasks']

    check_directory(cfg['PATH'])
    check_directory(cfg['TMPPATH'])
    launch_editor(cfg)

def main():
    _main(env=os.environ, args=vars(get_argument_parser().parse_args()))

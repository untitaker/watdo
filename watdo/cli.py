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
from os import environ as env
import subprocess
import os


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
        return
    for i, (description, func) in enumerate(changes):
        print(u'{}.  {}'.format(i, description))

    print('Enter changes you don\'t want to happen.')
    print('By number, space separated.')
    reverted = raw_input('> ')
    for i in (int(x.strip()) for x in reverted.split()):
        del changes[i]

    if not changes:
        print('No changes left.')
        return
    for description, func in changes:
        print(description)
        func()


def confirm(message='Are you sure? (Y/n)'):
    inp = raw_input(message).lower().strip()
    if not inp or inp == 'y':
        return True
    return False


def launch_editor(cfg, tmpfilename='todo.markdown'):
    tmpfilepath = os.path.join(cfg['TMPPATH'], tmpfilename)

    with open(tmpfilepath, 'wb+') as f:
        old_ids = editor.generate_tmpfile(f, cfg['PATH'])

    new_ids = None
    while new_ids is None:
        cmd = [cfg['EDITOR'], tmpfilepath]
        print('>>> ' + ' '.join(cmd))
        subprocess.call(cmd)

        with open(tmpfilepath, 'rb') as f:
            try:
                new_ids = editor.parse_tmpfile(f)
            except RuntimeError as e:
                print(e)
                print('Press enter to edit again...')
                raw_input()

    confirm_changes(editor.get_changes(old_ids, new_ids))
    os.remove(tmpfilepath)


def main():
    pjoin = os.path.join
    abspath = os.path.abspath
    cfg = {
        'PATH': abspath(env.get('WATDO_PATH')
                        or pjoin(env['HOME'], '.watdo/tasks/')),
        'TMPPATH': abspath(env.get('WATDO_TMPPATH')
                           or pjoin(env['HOME'], '.watdo/tmp/')),
        'EDITOR': env.get('WATDO_EDITOR') or env.get('EDITOR') or None
    }
    check_directory(cfg['PATH'])
    check_directory(cfg['TMPPATH'])
    launch_editor(cfg)

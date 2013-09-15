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
import tempfile
import os
import sys
import argparse
import ConfigParser


def check_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def path(p):
        p = os.path.expanduser(p)
        p = os.path.abspath(p)
        return p


def confirm(message='Are you sure? (Y/n)'):
    inp = raw_input(message).lower().strip()
    if not inp or inp == 'y':
        return True
    return False


def launch_editor(cfg, tmpfilesuffix='.markdown'):
    tmpfile = tempfile.NamedTemporaryFile(dir=cfg['TMPPATH'],
                                          suffix=tmpfilesuffix, delete=False)

    try:
        with tmpfile as f:
            old_ids = editor.generate_tmpfile(f, cfg,
                editor.walk_calendars(
                    cfg['PATH'],
                    all_tasks=cfg['SHOW_ALL_TASKS']
                )
            )

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

        changes = confirm_changes(editor.get_changes(old_ids, new_ids, cfg))
        for description, func in changes:
            print(description)
            func(cfg)
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
    for k, v in cfg.iteritems():
        if not v:
            continue
        yield k, v


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


def _main(env, args, cfg):
    
    def bail_out(msg):
        print(msg)
        sys.exit(1)
        
    new_cfg = {
        'PATH': path(
            env.get('WATDO_PATH') or
            cfg.get('path') or
            '~/.watdo/tasks/'
        ),
        'TMPPATH': path(
            env.get('WATDO_TMPPATH') or 
            cfg.get('tmppath') or
            '~/.watdo/tmp/'
        ),
        'EDITOR': (
            env.get('WATDO_EDITOR') or
            cfg.get('editor') or
            env.get('EDITOR') or
            bail_out('No editor could be determined. Make sure you\'ve got '
                     'either $WATDO_EDITOR or $EDITOR set.')
        ),
        'SHOW_ALL_TASKS': args['show_all_tasks']
    }

    check_directory(new_cfg['PATH'])
    check_directory(new_cfg['TMPPATH'])
    launch_editor(new_cfg)

def main():
    _main(env=os.environ,
          args=vars(get_argument_parser().parse_args()),
          cfg=get_config_parser(os.environ))

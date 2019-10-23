#!/usr/bin/python3
#
# Config action implementation.
#
# Copyright (c) 2018-2019 Xevo Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import yaml

from wst import (
    BUILD_TYPES,
    log,
    WSError
)
from wst.cmd import Command
from wst.conf import (
    get_ws_config,
    parse_manifest
)


def parse_bool_val(val):
    '''Parses a value meant to be interpreted as a bool. Accepts 0, 1, false,
       and true (with any casing). Raises an exception if none match.'''
    if val is None:
        return True

    if val == '0':
        return False

    if val == '1':
        return True

    val = val.lower()
    if val == 'false':
        return False
    elif val == 'true':
        return True

    raise WSError('value "%s" is not a valid boolean' % val)


def _escape_commas(s):
    '''Turns "\\," into ",".'''
    return s.replace('\\,', ',')


def parse_build_args(val):
    '''Parses a value meant to be interpreted as comma-separated build
       arguments. \\, will escape a comma, so you can put a comma in a build
       argument.'''

    if val is None or val == '':
        return None

    split = []
    last_split = 0
    for i, c in enumerate(val):
        if c == ',':
            if not (i > 0 and val[i-1] == '\\'):
                substring = _escape_commas(val[last_split:i])
                split.append(substring)
                last_split = i+1
    split.append(_escape_commas(val[last_split:i+1]))
    return split


class Config(Command):
    '''The config command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the config command.'''
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            default=False,
            help='List the current workspace config')
        parser.add_argument(
            '-p', '--project',
            action='store',
            default=None,
            help='Set project-specific config')
        parser.add_argument(
            'options',
            action='store',
            nargs='*',
            help='Key-value options (format key=value')

    @classmethod
    def do(cls, ws, args):
        '''Executes the config command.'''
        config = get_ws_config(ws)
        if args.list:
            print(yaml.dump(config, default_flow_style=False), end='')
            return

        for arg in args.options:
            split = arg.split('=')
            split_len = len(split)
            key = split[0]
            if split_len == 1:
                val = None
            elif split_len == 2:
                val = split[1]
            else:
                val = '='.join(split[1:])

            project = args.project
            if project is not None:
                # Project-specific option.
                d = parse_manifest(args.root)
                if project not in d:
                    raise WSError('project "%s" not found' % project)

                can_taint = False
                if key == 'enable':
                    val = parse_bool_val(val)
                    can_taint = True
                elif key == 'args':
                    val = parse_build_args(val)
                    if val is None:
                        raise WSError('build args are not in the right format '
                                      '("args=key=val")')
                    can_taint = True
                else:
                    raise WSError('project key "%s" not found' % key)

                try:
                    proj_config = config['projects'][project]
                except KeyError:
                    proj_config = {}
                    config['projects'][project] = proj_config

                if can_taint and proj_config[key] != val:
                    log('tainting project %s' % project)
                    proj_config['taint'] = True

                proj_config[key] = val

            else:
                # Global option.
                if key == 'type':
                    if val is None or val not in BUILD_TYPES:
                        raise WSError('"type" key must be one of %s'
                                      % str(BUILD_TYPES))
                    if config[key] != val:
                        for proj_config in config['projects'].values():
                            proj_config['taint'] = True

                config[key] = val

#!/usr/bin/python3
#
# Config action implementation.
#
# Copyright (c) 2018 Xevo Inc. All rights reserved.
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

import copy
import yaml

from wst import WSError
from wst.cmd import Command
from wst.conf import (
    BUILD_TYPES,
    get_ws_config,
    parse_manifest,
    update_config
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

        old_config = copy.deepcopy(config)
        for arg in args.options:
            split = arg.split('=')
            split_len = len(split)
            if split_len == 1:
                key = split[0]
                val = None
            elif split_len == 2:
                key = split[0]
                val = split[1]
            else:
                raise WSError('option argument %s invalid. format is val or '
                              'key=value' % arg)

            project = args.project
            if project is not None:
                # Project-specific option.
                d = parse_manifest(args.root)
                if project not in d:
                    raise WSError('project "%s" not found' % project)

                if key == 'enable':
                    val = parse_bool_val(val)
                else:
                    raise WSError('project key "%s" not found' % key)

                try:
                    proj_config = config['projects'][project]
                except KeyError:
                    proj_config = {}
                    config['projects'][project] = proj_config

                proj_config[key] = val

            else:
                # Global option.
                if key == 'type':
                    if val not in BUILD_TYPES:
                        raise WSError('"type" key must be one of %s'
                                      % BUILD_TYPES)
                    current_key = config.get(key, None)
                    if current_key != val:
                        config['taint'] = True

                config[key] = val

        if config != old_config:
            update_config(ws, config)

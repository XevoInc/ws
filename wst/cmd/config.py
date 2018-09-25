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

import yaml

from wst import WSError
from wst.cmd import Command
from wst.conf import (
    get_ws_config,
    update_config,
    VALID_CONFIG
)


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
            if len(split) != 2:
                raise WSError('option argument %s invalid. format is key=value'
                              % arg)
            key, val = split
            if key not in VALID_CONFIG:
                raise WSError('unknown key %s' % key)
            if val not in VALID_CONFIG[key]:
                raise WSError('unknown value %s' % val)
            if key == 'type' and config[key] != val:
                config['taint'] = True
            config[key] = val

        update_config(ws, config)

#!/usr/bin/python3
#
# List action implementation.
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

import os

from wst.cmd import Command
from wst.conf import (
    get_default_ws_name,
    get_manifest_link_name,
    parse_manifest
)


class List(Command):
    '''The list command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the list subcmd.'''
        parser.add_argument(
            '-w', '--workspaces',
            action='store_true',
            dest='list_workspaces',
            default=False,
            help='List workspaces instead of projects')

    @classmethod
    def do(cls, _, args):
        '''Executes the list subcmd.'''
        if args.list_workspaces:
            dirs = os.listdir(args.root)
            for ws in dirs:
                if ws == get_default_ws_name():
                    continue
                if ws == get_manifest_link_name():
                    continue
                print(ws)
        else:
            d = parse_manifest(args.root)
            for proj in d:
                print(proj)

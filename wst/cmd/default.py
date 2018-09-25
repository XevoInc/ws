#!/usr/bin/python3
#
# Default action implementation.
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

from wst import WSError
from wst.cmd import Command
from wst.conf import (
    get_default_ws_link,
    get_ws_dir
)
from wst.shell import (
    remove,
    symlink
)


class Default(Command):
    '''The default command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the default command.'''
        parser.add_argument(
            metavar='workspace',
            dest='default_ws',
            action='store',
            default=None,
            nargs='?',
            help='Workspace to make the default')

    @classmethod
    def do(cls, _, args):
        '''Executes the default command.'''
        link = get_default_ws_link(args.root)
        if args.default_ws is None:
            # Just report what the default currently is.
            dest = os.path.basename(os.path.realpath(link))
            print(dest)
            return

        ws_dir = get_ws_dir(args.root, args.default_ws)

        remove(link)
        if not os.path.exists(ws_dir):
            raise WSError('Cannot make non-existent workspace %s the default' %
                          args.default_ws)

        symlink(args.default_ws, link)

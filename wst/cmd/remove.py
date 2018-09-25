#!/usr/bin/python3
#
# Remove action implementation.
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
    rmtree,
    symlink
)


class Remove(Command):
    '''The remove command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the remove command.'''
        parser.add_argument(
            metavar='workspace',
            dest='remove_ws',
            action='store',
            help='Workspace to remove')
        parser.add_argument(
            '-d', '--default',
            action='store',
            default=None,
            help='New default workspace')

    @classmethod
    def do(cls, _, args):
        '''Executes the remove command.'''
        ws_dir = get_ws_dir(args.root, args.remove_ws)
        if not os.path.exists(ws_dir):
            raise WSError('workspace %s does not exist' % args.remove_ws)

        if args.default is not None:
            default_ws_dir = get_ws_dir(args.root, args.default)
            if not os.path.exists(default_ws_dir):
                raise WSError('workspace %s does not exist' % args.default)

        default_link = get_default_ws_link(args.root)
        is_default = (os.readlink(default_link) == args.remove_ws)
        if is_default:
            # If the deleted workspace is the default, force the user to choose
            # a new one.
            if args.default is None:
                raise WSError('trying to remove the default workspace; must '
                              'specify a new default via -d/--default')
        elif args.default:
            raise WSError('-d/--default is not applicable unless you are '
                          'removing the default workspace')

        # We are good to go.
        rmtree(ws_dir)
        if is_default:
            remove(default_link)
            symlink(args.default, default_link)

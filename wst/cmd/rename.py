#!/usr/bin/python3
#
# Rename action implementation.
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
from wst.conf import (
    get_build_dir,
    get_default_ws_link,
    get_ws_dir,
    parse_manifest
)
from wst.shell import (
    remove,
    rename,
    symlink
)


def args(parser):
    '''Populates the argument parser for the rename subcmd.'''
    parser.add_argument(
        metavar='old-workspace-name',
        dest='old_ws',
        action='store',
        help='Old workspace name')
    parser.add_argument(
        metavar='new-workspace-name',
        dest='new_ws',
        action='store',
        help='New workspace name')


def handler(ws, args):
    '''Executes the rename subcmd.'''
    old_ws_dir = get_ws_dir(args.root, args.old_ws)
    if not os.path.exists(old_ws_dir):
        raise WSError('Workspace %s does not exist' % args.old_ws)

    d = parse_manifest(args.root)
    for proj in d:
        build_dir = get_build_dir(old_ws_dir, proj)
        if os.path.exists(build_dir):
            raise WSError('cannot rename a workspace that contains build '
                          'artifacts, as some builds contain absolute paths '
                          'and are thus not relocatable. Please force-clean '
                          'this workspace first and then rename it.')

    new_ws_dir = get_ws_dir(args.root, args.new_ws)
    if os.path.exists(new_ws_dir):
        raise WSError('Workspace %s already exists; please delete it first if '
                      'you want to do this rename' % args.new_ws)

    rename(old_ws_dir, new_ws_dir)
    default_link = get_default_ws_link(args.root)
    if os.readlink(default_link) == args.old_ws:
        remove(default_link)
        symlink(args.new_ws, default_link)

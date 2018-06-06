#!/usr/bin/python3
#
# Init action implementation.
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

import errno
import os

from wst import WSError
from wst.conf import (
    BUILD_TYPES,
    get_checksum_dir,
    get_default_ws_link,
    get_toplevel_build_dir,
    get_ws_dir,
    update_config
)


def args(parser):
    '''Populates the argument parser for the init subcmd.'''
    parser.add_argument(
        metavar='workspace',
        dest='init_ws',
        action='store',
        default=None,
        nargs='?',
        help='Workspace to initialize')

    parser.add_argument(
        '-t', '--type',
        action='store',
        choices=BUILD_TYPES,
        default='debug',
        help='Workspace type')


def handler(_, args):
    '''Executes the init subcmd.'''
    if args.root is None:
        root = '.ws'
    else:
        root = args.root

    if args.init_ws is None:
        ws = 'ws'
    else:
        ws = args.init_ws
    ws_dir = get_ws_dir(root, ws)

    if os.path.exists(ws_dir):
        raise WSError('Cannot initialize already existing workspace %s' % ws)

    try:
        os.mkdir(root)
        new = True
    except OSError as e:
        new = False
        if e.errno != errno.EEXIST:
            raise

    os.mkdir(ws_dir)

    if new:
        # This is a brand new .ws directory, so populate the initial
        # directories.
        link = get_default_ws_link(root)
        os.symlink(ws, link)
        os.mkdir(get_toplevel_build_dir(ws_dir))
        os.mkdir(get_checksum_dir(ws_dir))
        config = {
            'type': args.type,
            'taint': False
        }
        update_config(ws_dir, config)

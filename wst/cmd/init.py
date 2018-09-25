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
from wst.cmd import Command
from wst.conf import (
    BUILD_TYPES,
    get_checksum_dir,
    get_default_ws_link,
    get_default_ws_name,
    get_default_manifest_name,
    get_manifest_link,
    get_manifest_link_name,
    get_toplevel_build_dir,
    get_ws_dir,
    parse_manifest_file,
    update_config
)
from wst.shell import (
    mkdir,
    symlink
)


MANIFEST_SOURCES = ('fs', 'repo')


def _is_subdir(a, b):
    '''Returns True if a is a sub-directory of b.'''
    a = os.path.abspath(a)
    b = os.path.abspath(b)

    return os.path.commonpath((a, b)) == b


class Init(Command):
    '''The list command.'''
    @classmethod
    def args(cls, parser):
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
        parser.add_argument(
            '-m', '--manifest',
            action='store',
            default=get_default_manifest_name(),
            help='ws manifest path')
        parser.add_argument(
            '-s', '--manifest-source',
            action='store',
            choices=MANIFEST_SOURCES,
            default='repo',
            help=('If -m is specified, what the path is relative to (see '
                  'README for details)'))

    @classmethod
    def do(cls, _, args):
        '''Executes the init command.'''
        if args.root is None:
            root = '.ws'
        else:
            root = args.root

        if args.init_ws is None:
            ws = 'ws'
        else:
            reserved = (get_default_ws_name(), get_manifest_link_name())
            for name in reserved:
                if args.init_ws == name:
                    raise WSError('%s is a reserved name; please choose a '
                                  'different name' % name)
            ws = args.init_ws
        ws_dir = get_ws_dir(root, ws)

        if os.path.exists(ws_dir):
            raise WSError('Cannot initialize already existing workspace %s'
                          % ws)

        if args.manifest_source == 'repo':
            parent = os.path.realpath(os.path.join(root, os.pardir))
            base = os.path.join(parent, '.repo', 'manifests')
        elif args.manifest_source == 'fs':
            base = '.'
        else:
            raise NotImplemented('Manifest source %s should be implemented'
                                 % args.manifest_source)
        manifest = os.path.join(base, args.manifest)
        if os.path.isdir(manifest):
            # If -m points to a directory instead of a file, assume there is a
            # file with the default manifest name inside.
            manifest = os.path.join(manifest, get_default_manifest_name())

        # Use a relative path for anything inside the parent of .ws and an
        # absolute path for anything outside. This is to maximize
        # relocatability for groups of git repos (e.g. using submodules,
        # repo-tool, etc.).
        manifest = os.path.abspath(manifest)
        parent = os.path.realpath(os.path.join(root, os.pardir))
        if _is_subdir(manifest, parent):
            manifest = os.path.relpath(manifest, root)
        else:
            manifest = os.path.abspath(manifest)

        # Make sure the given manifest is sane.
        if os.path.isabs(manifest):
            abs_manifest = manifest
        else:
            abs_manifest = os.path.abspath(os.path.join(root, manifest))
        parse_manifest_file(root, abs_manifest)

        try:
            mkdir(root)
            new_root = True
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            new_root = False

        try:
            mkdir(ws_dir)
            new_ws = True
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            new_ws = False

        if new_ws:
            # This is a brand-new workspace, so populate the initial workspace
            # directories.
            mkdir(get_toplevel_build_dir(ws_dir))
            mkdir(get_checksum_dir(ws_dir))
            config = {
                'type': args.type,
                'taint': False
            }
            update_config(ws_dir, config)

        if new_root:
            # This is a brand new root .ws directory, so populate the initial
            # symlink defaults.
            symlink(ws, get_default_ws_link(root))
            symlink(manifest, get_manifest_link(root))

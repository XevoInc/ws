#!/usr/bin/python3
#
# Clean action implementation.
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
import logging
import os

from wst import (
    dry_run,
    WSError
)
from wst.cmd import Command
from wst.conf import (
    get_build_dir,
    get_build_env,
    get_builder,
    get_install_dir,
    get_source_dir,
    get_ws_config,
    invalidate_checksum,
    parse_manifest,
    update_config
)
from wst.shell import rmtree


def _force_clean(ws, proj):
    '''Performs a force-clean of a project, removing all files instead of
    politely calling the clean function of the underlying build system.'''
    build_dir = get_build_dir(ws, proj)
    logging.debug('removing %s' % build_dir)
    if dry_run():
        return
    try:
        rmtree(build_dir)
    except OSError as e:
        if e.errno == errno.ENOENT:
            logging.debug('%s already removed' % build_dir)
        else:
            raise

    config = get_ws_config(ws)
    config['taint'] = False
    update_config(ws, config)


def _polite_clean(root, ws, proj, d):
    '''Performs a polite-clean of a project, calling the underlying build
    system of a project and asking it to clean itself.'''
    builder = get_builder(d, proj)
    build_dir = get_build_dir(ws, proj)
    if not os.path.exists(build_dir):
        return

    build_env = get_build_env(ws, d, proj)
    prefix = get_install_dir(ws, proj)
    source_dir = get_source_dir(root, d, proj)
    builder.clean(proj, prefix, source_dir, build_dir, build_env)


def _clean(root, ws, proj, force, d):
    '''Cleans a project, forcefully or not.'''
    invalidate_checksum(ws, proj)

    if force:
        _force_clean(ws, proj)
    else:
        _polite_clean(root, ws, proj, d)


class Clean(Command):
    '''The clean command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the clean command.'''
        parser.add_argument(
            'projects',
            action='store',
            nargs='*',
            help='Clean project(s)')
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            default=False,
            help='Force-clean (remove the build directory')

    @classmethod
    def do(cls, ws, args):
        '''Executes the clean command.'''
        # Validate.
        d = parse_manifest(args.root)
        for project in args.projects:
            if project not in d:
                raise WSError('unknown project %s' % project)

        if len(args.projects) == 0:
            projects = d.keys()
        else:
            projects = args.projects

        for project in projects:
            _clean(args.root, ws, project, args.force, d)

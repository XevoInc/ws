#!/usr/bin/python3
#
# Build action implementation.
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
import multiprocessing
import os

from wst import WSError
from wst.cmd import Command
from wst.conf import (
    calculate_checksum,
    dependency_closure,
    get_build_dir,
    get_build_env,
    get_builder,
    get_install_dir,
    get_proj_dir,
    get_source_dir,
    get_source_link,
    get_stored_checksum,
    get_ws_config,
    get_ws_dir,
    invalidate_checksum,
    parse_manifest,
    set_stored_checksum
)
from wst.shell import (
    rmtree,
    symlink,
    mkdir
)


def _build(root, ws, proj, d, current, ws_config, force):
    '''Builds a given project.'''
    source_dir = get_source_dir(root, d, proj)
    if not force:
        stored = get_stored_checksum(ws, proj)
        if current == stored:
            logging.debug('checksum for %s is current; skipping' % proj)
            return True
    else:
        logging.debug('forcing a build of %s' % proj)

    # Make the project directory if needed.
    proj_dir = get_proj_dir(ws, proj)
    try:
        mkdir(proj_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Make the build directory if needed.
    build_dir = get_build_dir(ws, proj)
    needs_configure = os.path.exists(build_dir)
    try:
        mkdir(build_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        needs_configure = False
    else:
        needs_configure = True

    # Populate the convenience source link.
    source_link = get_source_link(ws, proj)
    if not os.path.exists(source_link):
        source_dir = get_source_dir(root, d, proj)
        symlink(source_dir, source_link)

    # Invalidate the checksums for any downstream projects.
    for downstream_dep in d[proj]['downstream']:
        invalidate_checksum(ws, downstream_dep)

    # Add envs to find all projects on which this project is dependent.
    build_env = get_build_env(ws, d, proj)

    # Configure.
    builder = get_builder(d, proj)
    prefix = get_install_dir(ws, proj)
    if needs_configure:
        success = builder.conf(
            proj,
            prefix,
            source_dir,
            build_dir,
            build_env,
            ws_config['type'],
            d[proj]['options'])
        if not success:
            # Remove the build directory if we failed so that we are forced to
            # re-run configure next time.
            rmtree(build_dir)
            return False

    # Build.
    success = builder.build(
        proj,
        prefix,
        source_dir,
        build_dir,
        build_env,
        d[proj]['options'])
    if success:
        set_stored_checksum(ws, proj, current)

    return success


class Build(Command):
    '''The build command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the build command.'''
        parser.add_argument(
            'projects',
            action='store',
            nargs='*',
            help='Build a particular project or projects')
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            default=False,
            help='Force a build')

    @classmethod
    def do(cls, ws, args):
        '''Executes the build subcmd.'''
        ws_config = get_ws_config(get_ws_dir(args.root, ws))
        if ws_config['taint']:
            raise WSError('Workspace is tainted from a config change; please '
                          'do:\n'
                          'ws clean --force\n'
                          'And then build again')

        d = parse_manifest(args.root)

        # Validate.
        for project in args.projects:
            if project not in d:
                raise WSError('unknown project %s' % project)

        if len(args.projects) == 0:
            projects = d.keys()
        else:
            projects = args.projects

        # Build in reverse-dependency order.
        order = dependency_closure(d, projects)

        # Get all checksums; since this is a nop build bottle-neck, do it in
        # parallel. On my machine, this produces a ~20% speedup on a nop
        # "build-all".
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        src_dirs = [get_source_dir(args.root, d, proj) for proj in order]
        checksums = pool.map(calculate_checksum, src_dirs)

        for i, proj in enumerate(order):
            logging.info('Building %s' % proj)
            checksum = checksums[i]
            success = _build(
                args.root,
                ws,
                proj,
                d,
                checksum,
                ws_config,
                args.force)
            if not success:
                raise WSError('%s build failed' % proj)

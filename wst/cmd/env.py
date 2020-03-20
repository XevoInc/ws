#!/usr/bin/python3
#
# Env action implementation.
#
# Copyright (c) 2018-2019 Xevo Inc. All rights reserved.
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

import argparse
import os

from wst import (
    WSError,
    log
)
from wst.cmd import Command
from wst.conf import (
    get_build_dir,
    get_build_env,
    merge_var,
    parse_manifest
)
from wst.shell import get_shell


class Env(Command):
    '''The env command.'''
    @classmethod
    def args(cls, parser):
        group = parser.add_mutually_exclusive_group()
        '''Populates the argument parser for the env command.'''
        group.add_argument(
            '-b', '--build-dir',
            action='store_true',
            default=False,
            help='Enter the env from the build directory instead of the '
                 'current directory')
        group.add_argument(
            '-c', '--current-dir',
            action='store',
            default=None,
            help='The directory from which the command will be run')

        parser.add_argument(
            'project',
            action='store',
            help='Enter the build environment for a particular project')
        parser.add_argument(
            'command',
            action='store',
            nargs=argparse.REMAINDER,
            help='Command to run inside the given environment')

    @classmethod
    def do(cls, ws, args):
        '''Executes the env command.'''
        build_dir = get_build_dir(ws, args.project)
        if not os.path.isdir(build_dir):
            raise WSError('build directory for %s doesn\'t exist; have you '
                          'built it yet?' % args.project)

        d = parse_manifest(args.root)
        build_env = get_build_env(ws, d, args.project)

        # Add the build directory to the path for convenience of running
        # non-installed binaries, such as unit tests.
        merge_var(build_env, 'PATH', [build_dir])

        if len(args.command) > 0:
            cmd = args.command
        else:
            cmd = [get_shell()]

        exe = os.path.basename(cmd[0])
        if exe == 'bash':
            # Tweak the prompt to make it obvious we're in a special env.
            prompt = ('\\[\033[1;32m\\][ws:%s env]\\[\033[m\\] \\u@\\h:\\w\\$ '  # noqa: E501
                      % args.project)
            build_env['PS1'] = prompt
            cmd.insert(1, '--norc')

        # Set an env var so the user can easily cd $WSBUILD and run tests or
        # similar inside the build directory.
        build_env['WSBUILD'] = build_dir

        log('execing with %s build environment: %s' % (args.project, cmd))

        if args.build_dir:
            args.current_dir = build_dir

        if args.current_dir is not None:
            os.chdir(args.current_dir)

        os.execvpe(cmd[0], cmd, build_env)

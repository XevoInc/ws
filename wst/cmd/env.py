#!/usr/bin/python3
#
# Env action implementation.
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

import argparse
import logging
import os

from wst import WSError
from wst.conf import (
    get_build_dir,
    get_build_env,
    parse_manifest
)
from wst.shell import get_shell


def args(parser):
    '''Populates the argument parser for the env subcmd.'''
    parser.add_argument(
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


def handler(ws, args):
    '''Executes the env subcmd.'''
    build_dir = get_build_dir(ws, args.project)
    if not os.path.isdir(build_dir):
        raise WSError('build directory for %s doesn\'t exist; have you built '
                      'it yet?' % args.project)

    d = parse_manifest(args.root)
    build_env = get_build_env(ws, d, args.project, True)

    if len(args.command) > 0:
        cmd = args.command
    else:
        cmd = [get_shell()]

    exe = os.path.basename(cmd[0])
    if exe in ('bash', 'sh'):
        suffix = '\\[\033[1;32m\\][ws-%s-env]\\[\033[m\\]$ ' % args.project
        if exe == 'bash':
            # Tweak the prompt to make it obvious we're in a special env.
            cmd.insert(1, '--norc')
            prompt = '\\u@\h:\w %s' % suffix
        elif exe == 'sh':
            # sh doesn't support \u and other codes.
            prompt = suffix
        build_env['PS1'] = prompt

    logging.debug('execing with %s build environment: %s'
                  % (args.project, cmd))

    if args.current_dir is None:
        current_dir = get_build_dir(ws, args.project)
    else:
        current_dir = args.current_dir
    os.chdir(current_dir)

    os.execvpe(cmd[0], cmd, build_env)

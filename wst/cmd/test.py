#!/usr/bin/python3
#
# Test action implementation.
#
# Copyright (c) 2020 Xevo Inc. All rights reserved.
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

from wst import (
    WSError,
    log
)
from wst.cmd import Command
from wst.conf import (
    expand_vars,
    get_build_dir,
    get_build_env,
    parse_manifest)
from wst.shell import call_test


def _test(root, ws, proj, cmds, env):
    '''Tests a given project.'''
    for props in cmds:
        cwd = expand_vars(props['cwd'], ws, proj, env)
        cmds = props['cmds']
        for cmd in cmds:
            cmd = expand_vars(cmd, ws, proj, env)
            success = call_test(cmd.split(), cwd=cwd, env=env)
            if not success:
                repro_cmd = '(cd %s && ws env %s %s)' % (cwd, proj, cmd)
                raise WSError('''
%s tests failed. You can reproduce this failure by running:
%s''' % (proj, repro_cmd))


class Test(Command):
    '''The test command.'''
    @classmethod
    def args(cls, parser):
        '''Populates the argument parser for the build command.'''
        parser.add_argument(
            'projects',
            action='store',
            nargs='*',
            help='Test a particular project or projects')

    @classmethod
    def do(cls, ws, args):
        '''Executes the test subcmd.'''
        d = parse_manifest(args.root)

        # Validate.
        for project in args.projects:
            if project not in d:
                raise WSError('unknown project %s' % project)

        if len(args.projects) == 0:
            projects = d.keys()
        else:
            projects = args.projects

        for proj in projects:
            build_dir = get_build_dir(ws, proj)
            if not os.path.isdir(build_dir):
                raise WSError('build directory for %s doesn\'t exist; have '
                              'you built it yet?' % proj)

            if 'tests' not in d[proj]:
                raise WSError('no test configured for %s' % proj)

        for proj in projects:
            log('testing %s' % proj)
            build_env = get_build_env(ws, d, proj)
            cmds = d[proj]['tests']
            _test(args.root, ws, proj, cmds, build_env)

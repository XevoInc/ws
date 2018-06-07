#!/usr/bin/python3
#
# setuptools builder.
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
import shutil

from wst.builder import Builder
from wst.shell import call_build


class SetuptoolsBuilder(Builder):
    '''A setuptools builder.'''
    @classmethod
    def conf(cls, proj, prefix, build_dir, source_dir, env, build_type):
        '''Calls configure using setuptools.'''
        # setuptools doesn't have a configure step.
        return True


    @classmethod
    def build(cls, proj, source_dir, build_dir, env):
        '''Calls build using setuptools.'''

        # setuptools requires everything in PYTHONPATH to exist already, so create
        # any directories needed.
        paths = env['PYTHONPATH'].split(':')
        for path in paths:
            if not path.startswith(build_dir):
                continue

            # Found our path. We can assume the build directory already exists.
            assert(path.startswith(build_dir))
            path = path[len(build_dir)+1:]
            components = path.split(os.sep)
            for i in range(len(components)):
                full_path = os.sep.join(components[:i+1])
                full_path = os.path.join(build_dir, full_path)
                os.mkdir(full_path)

        return call_build(
            ('python3',
             'setup.py',
             'install',
             '--prefix=%s' % build_dir),
            cwd=source_dir,
            env=env)


    @classmethod
    def clean(cls, proj, build_dir, env):
        '''Calls clean using setuptools.'''
        # setuptools doesn't have a clean function.
        shutil.rmtree(build_dir)

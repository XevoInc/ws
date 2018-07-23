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

        return call_build(
            ('python3',
             'setup.py',
             'egg_info',
             '--egg-base=%s' % build_dir,
             'build',
             '--build-base=%s' % build_dir,
             'install',
             '--prefix=%s' % build_dir),
            cwd=source_dir,
            env=env)

    @classmethod
    def clean(cls, proj, build_dir, env):
        '''Calls clean using setuptools.'''
        # setuptools doesn't have a clean function.
        shutil.rmtree(build_dir)

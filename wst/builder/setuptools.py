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
import sys

from wst.builder import Builder
from wst.shell import call_build


class SetuptoolsBuilder(Builder):
    '''A setuptools builder.'''

    _PYTHON_LIB_DIR = os.path.join(
        'lib',
        'python%d.%d' % (sys.version_info[0], sys.version_info[1]),
        'site-packages')

    @classmethod
    def env(cls, proj, build_dir, env):
        '''Sets up environment tweaks for setuptools.'''
        # Import here to prevent a circular import.
        from wst.conf import merge_var

        # setuptools won't install into a --prefix unless
        # PREFIX/lib/pythonX.Y/site-packages is in PYTHONPATH, so we'll add it
        # in manually.
        python_path = os.path.join(build_dir, cls._PYTHON_LIB_DIR)
        merge_var(env, 'PYTHONPATH', [python_path])

    @classmethod
    def conf(cls, proj, prefix, build_dir, source_dir, env, build_type):
        '''Calls configure using setuptools.'''
        # setuptools doesn't have a configure step.
        return True

    @classmethod
    def build(cls, proj, source_dir, build_dir, env):
        '''Calls build using setuptools.'''

        # Some packages require PREFIX/lib/pythonX.Y/site-packages to exist
        # before we can install into it.
        path = build_dir
        for component in cls._PYTHON_LIB_DIR.split(os.sep):
            path = os.path.join(path, component)
            try:
                os.mkdir(path)
            except FileExistsError:
                break

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

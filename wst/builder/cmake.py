#!/usr/bin/python3
#
# cmake builder.
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


import multiprocessing

from wst.builder import Builder
from wst.shell import (
    call_build,
    call_clean,
    call_configure
)


class CMakeBuilder(Builder):
    '''A CMake builder.'''
    @classmethod
    def env(cls, proj, prefix, build_dir, env):
        '''Sets up environment tweaks for cmake.'''
        pass

    @classmethod
    def conf(cls,
             proj,
             prefix,
             source_dir,
             build_dir,
             env,
             build_type,
             options):
        '''Calls configure using CMake.'''
        cmd = [
            'cmake',
            '-DCMAKE_BUILD_TYPE=%s' % build_type,
            '-DCMAKE_INSTALL_PREFIX=%s' % prefix]
        for opt in options:
            cmd.extend(opt)
        cmd.append(source_dir)
        return call_configure(cmd, env=env, cwd=build_dir)

    @classmethod
    def build(cls, proj, prefix, source_dir, build_dir, env, options):
        '''Calls build using CMake.'''
        return call_build(
            ('make',
             '-C', build_dir,
             '-j', str(multiprocessing.cpu_count()+1),
             'install'),
            env=env)

    @classmethod
    def clean(cls, proj, prefix, source_dir, build_dir, env):
        '''Calls clean using CMake.'''
        return call_clean(('make', '-C', build_dir, 'clean'), env=env)

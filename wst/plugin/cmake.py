#!/usr/bin/python3
#
# cmake plugin for ws.
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

from wst.shell import (
    call_build,
    call_clean,
    call_configure
)


def conf_cmake(proj, prefix, build_dir, source_dir, env, build_type):
    '''Calls configure using CMake.'''
    cmd = (
        'cmake',
        '-DCMAKE_BUILD_TYPE', build_type,
        '-DCMAKE_INSTALL_PREFIX', prefix,
        build_dir,
        source_dir)
    return call_configure(cmd, env=env)


def build_cmake(proj, source_dir, build_dir, env):
    '''Calls build using CMake.'''
    return call_build(('make', '-j', multiprocessing.cpu_count()+1), env=env)


def clean_cmake(proj, build_dir, env):
    '''Calls clean using CMake.'''
    return call_clean(('make', '-C', build_dir, 'clean'), env=env)

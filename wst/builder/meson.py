#!/usr/bin/python3
#
# meson builder.
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

from wst.builder import Builder
from wst.shell import (
    call_build,
    call_clean,
    call_configure
)


class MesonBuilder(Builder):
    '''A meson builder.'''
    @classmethod
    def env(cls, proj, prefix, build_dir, env, builder_args):
        '''Sets up environment tweaks for meson.'''
        pass

    @classmethod
    def conf(cls,
             proj,
             prefix,
             source_dir,
             build_dir,
             env,
             build_type,
             builder_args,
             args):
        '''Calls configure using Meson.'''
        cmd = [
            'meson',
            '--buildtype', build_type,
            '--prefix', prefix]
        cmd.extend(args)
        cmd.append(build_dir)
        cmd.append(source_dir)
        return call_configure(cmd, env=env)

    @classmethod
    def build(cls,
              proj,
              prefix,
              source_dir,
              build_dir,
              env,
              targets,
              builder_args,
              args):
        '''Calls build using the Meson build itself.'''
        return call_build(('ninja', '-C', build_dir) + targets, env=env)

    @classmethod
    def clean(cls, proj, prefix, source_dir, build_dir, env, builder_args):
        '''Calls clean using the Meson build itself.'''
        return call_clean(('ninja', '-C', build_dir, 'clean'), env=env)

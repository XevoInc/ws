#!/usr/bin/python3
#
# Base class for builders.
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


class Builder(object):

    '''A builder, representing the interaction with an underlying build
    system, such as CMake or meson. Since this is really an interface and not a
    class, all methods on it should be class methods.'''
    @classmethod
    def env(cls, proj, prefix, build_dir, source_dir, env, build_type):
        raise NotImplementedError

    @classmethod
    def conf(cls, proj, prefix, build_dir, source_dir, env, build_type):
        raise NotImplementedError

    @classmethod
    def build(cls, proj, source_dir, build_dir, env):
        raise NotImplementedError

    @classmethod
    def clean(cls, proj, build_dir, env):
        raise NotImplementedError

#!/usr/bin/python3
#
# Shell handling functions.
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
import subprocess


from wst import (
    dry_run,
    log,
    log_cmd
)


def mkdir(path):
    '''Makes a directory.'''
    log('making directory %s' % path)
    if not dry_run():
        os.mkdir(path)


def symlink(dest, src):
    '''Makes a symlink from src to dest.'''
    log('making symlink %s --> %s' % (src, dest))
    if not dry_run():
        os.symlink(dest, src)


def rename(old, new):
    '''Renames the given path.'''
    log('renaming %s --> %s' % (old, new))
    if not dry_run():
        os.rename(old, new)


def remove(path):
    '''Removes the given path.'''
    log('removing %s' % path)
    if not dry_run():
        os.unlink(path)


def rmtree(path):
    '''Removes the given file or directory, recursively.'''
    log('recursively removing %s' % path)
    if not dry_run():
        shutil.rmtree(path)


def get_shell():
    '''Gets the current default shell.'''
    try:
        return os.environ['SHELL']
    except KeyError:
        # Default, should exist on all systems.
        return '/bin/sh'


def call(cmd, **kwargs):
    '''Calls a given command with the given environment, swallowing the
    output.'''
    log_cmd(cmd)
    if not dry_run():
        subprocess.check_call(cmd, **kwargs)


def call_output(cmd, env=None, text=True, override=False):
    '''Calls a given command with the given environment, returning the
    output. Note that we assume the output is UTF-8.'''
    log_cmd(cmd)
    if (not dry_run()) or override:
        out = subprocess.check_output(cmd, env=env)
        if text:
            out = out.decode('utf-8')
        return out


def call_git(repo, subcmd):
    '''Executes a git command in a given repository.'''
    return call_output(('git', '-C', repo) + subcmd, text=False)


def call_noexcept(op, cmd, **kwargs):
    '''Calls a given command, swallowing output, and returns False if the
    command failed. Normally, we would just crash with an exeception. This
    should be used for commands that are allowed to fail in a normal case.'''
    try:
        call(cmd, **kwargs)
    except subprocess.CalledProcessError:
        return False
    return True


def call_configure(cmd, **kwargs):
    '''Executes a configure command.'''
    return call_noexcept('configure', cmd, **kwargs)


def call_build(cmd, **kwargs):
    '''Executes a build command.'''
    return call_noexcept('build', cmd, **kwargs)


def call_clean(cmd, **kwargs):
    '''Executes a clean command.'''
    return call_noexcept('clean', cmd, **kwargs)

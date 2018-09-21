#!/usr/bin/python3
#
# General functions usable by the entire module.
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


import logging


class WSError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


_DRY_RUN = False
def dry_run():  # noqa: E302
    '''Retrieves the current dry run setting.'''
    global _DRY_RUN
    return _DRY_RUN


def set_dry_run():
    '''Sets whether or not to use dry run mode.'''
    global _DRY_RUN
    _DRY_RUN = True


def log(msg):
    '''Logs a message.'''
    logging.debug(msg)


def log_cmd(cmd):
    '''Logs a given command being run.'''
    log(' '.join(cmd))

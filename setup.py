#!/usr/bin/python3
#
# setuptools script for ws.
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
import setuptools
from wst.version import version


# Keep the long description in sync with the README.
script_dir = os.path.dirname(os.path.realpath(__file__))
readme_path = os.path.join(script_dir, 'README.md')
with open(readme_path, 'r') as f:
    long_desc = f.read()

setuptools.setup(
    name='wst',
    version=version(),
    description='A lightweight tool for managing a workspace of repositories',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    author='Martin Kelly',
    author_email='mkelly@xevo.com',
    license='BSD',
    python_requires='>=3',
    install_requires=['PyYAML'],
    packages=setuptools.find_packages(),
    scripts=['bin/ws'],
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Natural Language :: English',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 3 :: Only',
                 'Topic :: Software Development :: Build Tools',
                 ],
)

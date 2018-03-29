#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Setup script for texttaglib

Latest version can be found at https://github.com/letuananh/texttaglib

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2018, Le Tuan Anh <tuananh.ke@gmail.com>
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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

########################################################################

import io
import os
from setuptools import setup

import texttaglib


########################################################################

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


readme_file = 'README.rst' if os.path.isfile('README.rst') else 'README.md'
print("README file: {}".format(readme_file))
long_description = read(readme_file)

setup(
    name='texttaglib',
    version=texttaglib.__version__,
    url=texttaglib.__url__,
    project_urls={
        "Bug Tracker": "https://github.com/letuananh/texttaglib/issues",
        "Source Code": "https://github.com/letuananh/texttaglib/"
    },
    keywords="nlp",
    license=texttaglib.__license__,
    author=texttaglib.__author__,
    tests_require=['chirptext >= 0.1a9', 'puchikarui'],
    install_requires=['chirptext >= 0.1a9', 'puchikarui'],
    author_email=texttaglib.__email__,
    description=texttaglib.__description__,
    long_description=long_description,
    packages=['texttaglib'],
    package_data={'texttaglib': ['data/*.sql', 'data/*.gz']},
    include_package_data=True,
    platforms='any',
    test_suite='test',
    # Reference: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=['Programming Language :: Python',
                 'Development Status :: 2 - Pre-Alpha',
                 'License :: OSI Approved :: {}'.format(texttaglib.__license__),
                 'Environment :: Plugins',
                 'Intended Audience :: Education',
                 'Intended Audience :: Science/Research',
                 'Intended Audience :: Information Technology',
                 'Intended Audience :: Developers',
                 'Operating System :: OS Independent',
                 'Topic :: Text Processing',
                 'Topic :: Text Processing :: Linguistic',
                 'Topic :: Software Development :: Libraries :: Python Modules']
)

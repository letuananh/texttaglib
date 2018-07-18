# -*- coding: utf-8 -*-

'''
ORG-Mode support

Latest version can be found at https://github.com/letuananh/texttaglib

References:
    - WebVTT: The Web Video Text Tracks Format
        https://www.w3.org/2013/07/webvtt.html

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

import re
import os
import logging

from chirptext import chio


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


RE_TITLE = re.compile('#\+TITLE: (?P<title>.+)$')
RE_META = re.compile('- (?P<tag>.+) :: (?P<value>.+)$')


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

def _match_title(line):
    m = RE_TITLE.match(line)
    if m:
        return m.group('title')
    else:
        return None


def _match_meta(line):
    m = RE_META.match(line)
    if m:
        return (m.group('tag'), m.group('value'))
    else:
        return None


def _parse_stream(input_stream):
    title = None
    meta = []
    reading_header = True
    lines = []
    for idx, line in enumerate(input_stream):
        if idx == 0:
            m = _match_title(line)
            if m:
                title = m
                continue
        # not title
        if reading_header:
            m = _match_meta(line)
            if m:
                meta.append(m)
                continue
            else:
                # not a meta line
                reading_header = False
                if not line.strip():
                    # ignore the first empty line after meta lines
                    continue
        # add to lines
        lines.append(line)
    return (title, meta, lines)


def read(filepath, **kwargs):
    with chio.open(filepath, mode='r') as infile:
        title, meta, lines = _parse_stream(infile)
        meta.append(('Filename', os.path.basename(filepath)))
        for k, v in kwargs.items():
            meta.append((k, v))
    return (title, meta, lines)


def org_to_ttlig(title, meta, lines, line_processor=None):
    iglines = ['# TTLIG']
    # add title
    if title:
        iglines.append("Title: {}".format(title))
    # add meta
    for k, v in meta:
        iglines.append("{}: {}".format(k, v))
    # add an empty between meta and content
    if meta:
        iglines.append('')

    # add lines
    for line in lines:
        if line_processor:
            line_processor(line, iglines)
        else:
            iglines.append(line)
    return iglines

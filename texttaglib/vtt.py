# -*- coding: utf-8 -*-

'''
WebVTT support for TTL

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
import logging
import math

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------


def getLogger():
    return logging.getLogger(__name__)


WEBVTT = re.compile(r'(?P<hour>\d{2,}):(?P<min>\d{2}):(?P<sec>\d{2}.\d{3})')


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

def sec2ts(seconds):
    ''' Convert duration in seconds to VTT format (e.g. 01:53:47.262) '''
    try:
        seconds = float(seconds)
        if seconds < 0:
            raise ValueError("Timestamp cannot be smaller than 0")
    except Exception as e:
        raise ValueError("Invalid timestamp ({})".format(seconds)) from e
    min_base = math.floor(seconds / 60)
    ts_hour = math.floor(min_base / 60)
    ts_min = math.floor(min_base % 60)
    ts_sec = math.floor(seconds) % 60
    ts_msec = (seconds - int(seconds)) * 1000
    ts = "{:0>2.0f}:{:0>2.0f}:{:0>2.0f}.{:0>3.0f}".format(ts_hour, ts_min, ts_sec, ts_msec)
    return ts


def ts2sec(ts):
    ''' Convert VTT timestamp to seconds '''
    if not ts:
        raise ValueError("Timestamp cannot be empty")
    m = WEBVTT.match(ts)
    if not m:
        raise ValueError("Invalid VTT timestamp format ({})".format(ts))
    pd = m.groupdict()  # parts' dictionary
    secs = int(pd['hour']) * 3600
    secs += int(pd['min']) * 60
    secs += float(pd['sec'])
    return secs

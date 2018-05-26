#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test WebVTT support
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

import os
import io
import unittest
import logging

from texttaglib import vtt


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

class TestTTLIG(unittest.TestCase):

    def test_wrong_input(self):
        self.assertRaises(ValueError, lambda: vtt.sec2ts(None))
        self.assertRaises(ValueError, lambda: vtt.sec2ts(-5))
        self.assertRaises(ValueError, lambda: vtt.sec2ts("-5"))
        self.assertRaises(ValueError, lambda: vtt.sec2ts("5.a"))
        # ts2sec
        self.assertRaises(ValueError, lambda: vtt.ts2sec(None))
        self.assertRaises(ValueError, lambda: vtt.ts2sec('00:00:00.00'))  # wrong msec
        self.assertRaises(TypeError, lambda: vtt.ts2sec(self))

    def test_vtt_ts_util(self):
        print("Test WebVTT timestamp conversion functions")
        inp = 0
        expected_ts = '00:00:00.000'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        inp = 26
        expected_ts = '00:00:26.000'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        inp = "26.999"
        expected_ts = '00:00:26.999'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, float(inp))

        inp = 61
        expected_ts = '00:01:01.000'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        inp = 83.027000
        expected_ts = '00:01:23.027'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        inp = 186.963
        expected_ts = '00:03:06.963'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        inp = 7497.999
        expected_ts = '02:04:57.999'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)

        # more than 99 hours
        inp = 997497.999
        expected_ts = '277:04:57.999'
        ts = vtt.sec2ts(inp)
        out = vtt.ts2sec(ts)
        self.assertEqual(ts, expected_ts)
        self.assertEqual(out, inp)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()

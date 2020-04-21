#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test ORG-mode
Latest version can be found at https://github.com/letuananh/texttaglib

References:
    Python unittest documentation:
        https://docs.python.org/3/library/unittest.html

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

from texttaglib import orgmode


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_ORG = '''#+TITLE: まだらの紐
- author :: アーサー・コナン・ドイル
- genre :: 短編小説

同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
同様に、悲しみそのものを、それが悲しみであるという理由で愛する者や、それゆえ得ようとする者は、どこにもいない。
'''


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------


class TestOrgMode(unittest.TestCase):

    def test_title(self):
        title = orgmode._match_title('#+TITLE: まだらの紐\n')
        self.assertEqual(title, 'まだらの紐')

    def test_meta(self):
        k, v = orgmode._match_meta('- genre :: fiction')
        self.assertEqual((k, v), ('genre', 'fiction'))

    def test_parse(self):
        instream = io.StringIO(TEST_ORG)
        t, m, l = orgmode._parse_stream(instream)
        self.assertEqual(t, 'まだらの紐')
        self.assertEqual(m, [('author', 'アーサー・コナン・ドイル'), ('genre', '短編小説')])
        self.assertEqual(len(l), 3)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()

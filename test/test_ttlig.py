#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test TTL Interlinear Gloss
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
from collections import OrderedDict

from chirptext import io as chio

from texttaglib import ttl
from texttaglib import ttlig
from texttaglib.ttlig import IGStreamReader, TTLTokensParser


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------


class TestFurigana(unittest.TestCase):

    def test_parse_furigana(self):
        rubytext = ttlig.parse_furigana('')
        self.assertEqual(str(rubytext), '')
        self.assertEqual(rubytext.to_html(), '')

        self.assertRaises(ValueError, lambda: ttlig.parse_furigana(None))

        rubytext = ttlig.parse_furigana('{食/た}べる')
        self.assertEqual(str(rubytext), '食べる')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>食</rb><rt>た</rt></ruby>べる')

        rubytext = ttlig.parse_furigana('{面/おも}{白/しろ}い')
        self.assertEqual(str(rubytext), '面白い')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>面</rb><rt>おも</rt></ruby><ruby><rb>白</rb><rt>しろ</rt></ruby>い')

        rubytext = ttlig.parse_furigana('{漢字/かんじ}')
        self.assertEqual(str(rubytext), '漢字')
        self.assertEqual(rubytext.to_html(), '<ruby><rb>漢字</rb><rt>かんじ</rt></ruby>')

        rubytext = ttlig.parse_furigana('お{天/てん}{気/き}')
        self.assertEqual(str(rubytext), 'お天気')
        self.assertEqual(rubytext.to_html(), 'お<ruby><rb>天</rb><rt>てん</rt></ruby><ruby><rb>気</rb><rt>き</rt></ruby>')
        # weird cases
        rubytext = ttlig.parse_furigana('{{漢字/かんじ}}')
        self.assertEqual(str(rubytext), '{漢字}')
        self.assertEqual(rubytext.to_html(), '{<ruby><rb>漢字</rb><rt>かんじ</rt></ruby>}')

        rubytext = ttlig.parse_furigana('お{天/てん{気/き}')
        self.assertEqual(str(rubytext), 'お{天/てん気')  # first one won't be matched
        self.assertEqual(rubytext.to_html(), 'お{天/てん<ruby><rb>気</rb><rt>き</rt></ruby>')

    def test_TTL_tokenizer(self):
        parser = TTLTokensParser()
        tokens = parser.parse_ruby('{猫/ねこ} が {好/す}き です 。')
        actual = parser.delimiter.join(r.to_html() for r in tokens)
        expected = '<ruby><rb>猫</rb><rt>ねこ</rt></ruby> が <ruby><rb>好</rb><rt>す</rt></ruby>き です 。'
        self.assertEqual(expected, actual)
        # test parse_ruby
        actual = ttlig.make_ruby_html('ケーキ を {食/た}べた 。')
        expected = 'ケーキ を <ruby><rb>食</rb><rt>た</rt></ruby>べた 。'
        self.assertEqual(expected, actual)


class TestTTLIG(unittest.TestCase):

    def test_iter_stream(self):
        raw = io.StringIO('''# TTLIG
# This is a comment
I drink green tea.
I drink green_tea.

I have two cats.
I have two cat-s.
''')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['I drink green tea.', 'I drink green_tea.'], ['I have two cats.', 'I have two cat-s.']]
        self.assertEqual(groups, expected)

        # nothing
        raw = io.StringIO('''# TTLIG''')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = []
        self.assertEqual(groups, expected)
        raw = io.StringIO('')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = []
        self.assertEqual(groups, expected)
        raw = io.StringIO('a\n\nb')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['a'], ['b']]
        self.assertEqual(groups, expected)
        raw = io.StringIO('a\n#comment\nb')
        groups = [x for x in IGStreamReader._iter_stream(raw)]
        expected = [['a', 'b']]
        self.assertEqual(groups, expected)

    def test_read_header(self):
        inpath = os.path.join(TEST_DIR, 'data', 'testig_vi_explicit.txt')
        with chio.open(inpath) as infile:
            meta = ttlig.IGStreamReader._read_header(infile)
        expected = OrderedDict([('Language', 'Vietnamese'), ('Language code', 'vie'), ('Lines', 'orth translit gloss translat'), ('Author', 'Le Tuan Anh'), ('Date', 'May 25 2018')])
        self.assertEqual(meta, expected)

    def test_read_file(self):
        inpath = os.path.join(TEST_DIR, 'data', 'testig_jp_manual.txt')
        s1, s2 = ttlig.read(inpath)
        s1_json = {'_DataObject__extra_data': {}, 'tokens': '{猫/ねこ} が {好/す}き です 。', 'translit': 'neko ga suki desu .', 'gloss': 'cat SUBM likeable COP .', 'translat': 'I like cats.', 'text': '猫が好きです。', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': ''}
        s2_json = {"_DataObject__extra_data": {}, "tokens": "{雨/あめ} が {降/ふ}る 。", "translat": "It rains.", "text": "雨が降る。", "transliteration": "", "transcription": "", "morphtrans": "", "morphgloss": "", "wordgloss": "", "translation": ""}
        self.assertEqual(s1.to_dict(), s1_json)
        self.assertEqual(s2.to_dict(), s2_json)
        # test furigana
        s1_furi = '<ruby><rb>猫</rb><rt>ねこ</rt></ruby> が <ruby><rb>好</rb><rt>す</rt></ruby>き です 。'
        s2_furi = '<ruby><rb>雨</rb><rt>あめ</rt></ruby> が <ruby><rb>降</rb><rt>ふ</rt></ruby>る 。'
        self.assertEqual(ttlig.make_ruby_html(s1.tokens), s1_furi)
        self.assertEqual(ttlig.make_ruby_html(s2.tokens), s2_furi)

    def test_ttlig_auto(self):
        inpath = os.path.join(TEST_DIR, 'data', 'testig_jp_manual.txt')
        s1, s2 = ttlig.read(inpath)
        s1_dict = {'_DataObject__extra_data': {}, 'tokens': '{猫/ねこ} が {好/す}き です 。', 'translit': 'neko ga suki desu .', 'gloss': 'cat SUBM likeable COP .', 'translat': 'I like cats.', 'text': '猫が好きです。', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': ''}
        s2_dict = {'_DataObject__extra_data': {}, 'tokens': '{雨/あめ} が {降/ふ}る 。', 'translat': 'It rains.', 'text': '雨が降る。', 'transliteration': '', 'transcription': '', 'morphtrans': '', 'morphgloss': '', 'wordgloss': '', 'translation': ''}
        self.assertEqual(s1.to_dict(), s1_dict)
        self.assertEqual(s2.to_dict(), s2_dict)

    def test_read_empty_file(self):
        instream = io.StringIO('# TTLIG')
        sents = ttlig.read_stream(instream)
        self.assertEqual(sents, [])

    def test_read_invalid_ttlig(self):
        instream = io.StringIO('')
        self.assertRaises(Exception, lambda: ttlig.read_stream(instream))
        invalid_file = os.path.join(TEST_DIR, 'data', 'testig_invalid.txt')
        self.assertRaises(Exception, lambda: ttlig.read(invalid_file))


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()

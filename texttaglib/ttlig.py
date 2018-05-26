# -*- coding: utf-8 -*-

'''
TTLIG Interlinear Gloss Format

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

import re
import logging

from collections import OrderedDict

from chirptext import DataObject, piter
from chirptext import io as chio


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

# Source: https://en.wikipedia.org/wiki/Interlinear_gloss
# An interlinear text will commonly consist of some or all of the following, usually in this order, from top to bottom:
#     The original orthography (typically in italic or bold italic),
#     a conventional transliteration into the Latin alphabet,
#     a phonetic transcription,
#     a morphophonemic transliteration,
#     a word-by-word or morpheme-by-morpheme gloss, where morphemes within a word are separated by hyphens or other punctuation,
#     a free translation, which may be placed in a separate paragraph or on the facing page if the structures of the languages are too different for it to follow the text line by line.
class IGRow(DataObject):
    def __init__(self, text='', transliteration='', transcription='', morphtrans='', morphgloss='', wordgloss='', translation='', **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.text = text
        self.transliteration = transliteration
        self.transcription = transcription
        self.morphtrans = morphtrans
        self.morphgloss = morphgloss
        self.wordgloss = wordgloss
        self.translation = translation

    # Matrix alias
    @property
    def orth(self):
        return self.text

    @orth.setter
    def orth(self, value):
        self.text = value

    @property
    def translit(self):
        return self.transliteration

    @translit.setter
    def translit(self, value):
        self.transliteration = value

    @property
    def translat(self):
        return self.translation

    @translat.setter
    def translat(self, value):
        self.translation = value

    @property
    def gloss(self):
        return self.morphgloss

    @gloss.setter
    def gloss(self, value):
        self.morphgloss = value


class TTLIG(object):

    AUTO_LINES = ['transliteration', 'transcription', 'morphtrans', 'gloss']
    MANUAL_TAG = '__manual__'
    AUTO_TAG = '__auto__'
    KNOWN_LABELS = AUTO_LINES + ['ident', 'comment', 'orth', 'morphgloss', 'wordgloss', 'translation', 'text', 'translit', 'translat', 'source', 'vetted', 'judgement', 'phenomena', 'url', 'tokens', 'tsfrom', 'tsto', AUTO_TAG, MANUAL_TAG]

    def __init__(self, meta):
        self.meta = meta

    def row_format(self):
        if 'Lines' in self.meta:
            lines = self.meta['Lines'].strip()
            if lines:
                return self.meta['Lines'].strip().split()
        return []

    def _parse_row(self, line_list, line_tags):
        if not line_list:
            raise ValueError("Lines cannot be empty")
        if not line_tags or line_tags == [TTLIG.AUTO_TAG]:
            # auto
            # first line = text, last line = translation, transli
            if len(line_list) == 1:
                return IGRow(text=line_list[0])
            elif len(line_list) == 2:
                return IGRow(text=line_list[0], translation=line_list[-1])
            else:
                others = {k: v for k, v in zip(TTLIG.AUTO_LINES, line_list[1:-1])}
                return IGRow(text=line_list[0], translation=line_list[-1], **others)
        elif line_tags == [TTLIG.MANUAL_TAG]:
            line_dict = {}
            for line in line_list:
                tag_idx = line.find(':')
                if tag_idx == -1:
                    raise ValueError("Invalid line (no tag found) -> {}".format(line))
                _tag = line[:tag_idx].strip()
                _val = line[tag_idx + 1:].strip()
                if _tag not in TTLIG.KNOWN_LABELS:
                    getLogger().warning("Unknown tag was used {}: {}".format(_tag, _val))
                line_dict[_tag] = _val
            return IGRow(**line_dict)
        else:
            # just zip them
            if len(line_tags) != len(line_list):
                raise ValueError("Mismatch number of lines for {} - {}".format(line_tags, line_list))
            return IGRow(**{k: v for k, v in zip(line_tags, line_list)})

    def read_iter(self, stream):
        line_tags = self.row_format()
        for tag in line_tags:
            if tag not in TTLIG.KNOWN_LABELS:
                getLogger().warning("Unknown label in header: {}".format(tag))
        for row in IGStreamReader._iter_stream(stream):
            yield self._parse_row(row, line_tags)


class IGStreamReader(object):

    META_LINE = re.compile('(?P<key>[\w\s]+):\s*(?P<value>.*)')

    @staticmethod
    def _read_header(ig_stream):
        ''' Read the TTLIG header from a stream '''
        lines = piter(ig_stream)
        first = next(lines)
        if first.strip() != '# TTLIG':
            raise Exception("Invalid TTLIG header. TTLIG files must start with # TTLIG")
        meta = OrderedDict()
        for line in lines:
            if line.startswith("#"):
                continue
            m = IGStreamReader.META_LINE.match(line)
            if m:
                key = m['key'].strip()
                value = m['value']
                if key in meta:
                    getLogger().warning("Key {} is duplicated in the header".format(key))
                meta[key] = value
            else:
                break
        return meta

    @staticmethod
    def _iter_stream(ig_stream):
        lines = piter(ig_stream)
        current = []
        for line_raw in lines:
            line = line_raw.strip()
            if not line.startswith('#') and line:
                # not a comment or an empty line
                current.append(line)
            if not line or not lines.peep() or not lines.peep().value:
                if current:
                    yield current
                    current = []


def read_stream_iter(ttlig_stream):
    meta = IGStreamReader._read_header(ttlig_stream)
    ig_obj = TTLIG(meta)
    return ig_obj.read_iter(ttlig_stream)


def read_stream(ttlig_stream):
    ''' read TTLIG stream '''
    return [s for s in read_stream_iter(ttlig_stream)]


def read(ttlig_filepath):
    ''' Read TTLIG file '''
    with chio.open(ttlig_filepath, mode='r') as infile:
        return read_stream(infile)


FURIMAP = re.compile('\{(?P<text>\w+)/(?P<furi>\w+)\}')


class RubyToken(DataObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.groups is None:
            self.groups = []

    def append(self, group):
        self.groups.append(group)

    def text(self):
        return ''.join(str(x) for x in self.groups)

    def to_html(self):
        frags = []
        for g in self.groups:
            if isinstance(g, RubyFrag):
                frags.append(g.to_html())
            else:
                frags.append(str(g))
        return ''.join(frags)

    def __str__(self):
        return self.text()


class RubyFrag(DataObject):
    def __init__(self, text, furi, **kwargs):
        super().__init__(text=text, furi=furi, **kwargs)

    def __repr__(self):
        return "Ruby(text={}, furi={})".format(repr(self.text), repr(self.furi))

    def to_html(self):
        return "<ruby><rb>{}</rb><rt>{}</rt></ruby>".format(self.text, self.furi)

    def __str__(self):
        return self.text if self.text else ''


def parse_furigana(text):
    ''' Parse TTLRuby token '''
    if text is None:
        raise ValueError
    start = 0
    ruby = RubyToken()
    ms = [(m.groupdict(), m.span()) for m in FURIMAP.finditer(text)]
    # frag: ruby fragment
    for frag, (cfrom, cto) in ms:
        if start < cfrom:
            ruby.append(text[start:cfrom])
        ruby.append(RubyFrag(text=frag['text'], furi=frag['furi']))
        start = cto
    if start < len(text):
        ruby.append(text[start:len(text)])
    return ruby


class TTLTokensParser(object):
    ''' TTL Tokens parser '''
    def __init__(self, escapechar='\\', delimiter=' '):
        self.escapechar = escapechar
        self.delimiter = delimiter

    def parse(self, text):
        tokens = []
        current = []
        chars = piter(text)
        is_escaping = False
        for c in chars:
            if is_escaping:
                current.append(c)
                is_escaping = False
            elif c == self.escapechar:
                # add the next character to current token
                is_escaping = True
            elif c == self.delimiter:
                # flush
                if current:
                    tokens.append(''.join(current))
                    current = []
            else:
                current.append(c)
                # is last character
                if chars.peep() is None:
                    tokens.append(''.join(current))
                    current = []
        return tokens

    def parse_ruby(self, text):
        return [parse_furigana(t) for t in self.parse(text)]


DEFAULT_TTL_TOKEN_PARSER = TTLTokensParser()


def parse_ruby(text):
    return DEFAULT_TTL_TOKEN_PARSER.parse_ruby(text)


def make_ruby_html(text):
    tokens = parse_ruby(text)
    return DEFAULT_TTL_TOKEN_PARSER.delimiter.join(r.to_html() for r in tokens)

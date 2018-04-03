# -*- coding: utf-8 -*-

'''
TTL SQLite Data Access Layer

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

import logging

from chirptext import DataObject
from puchikarui import Schema, with_ctx
from texttaglib import ttl
from .data import INIT_TTL_SQLITE


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class Corpus(DataObject):
    pass


class CWLink(DataObject):
    pass


class TTLSQLite(Schema):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_file(INIT_TTL_SQLITE)
        # add tables
        self.add_table('corpus', ['ID', 'name', 'title'], proto=Corpus).set_id('ID')
        self.add_table('document', ['ID', 'name', 'title', 'lang', 'corpusID'],
                       proto=ttl.Document, alias='doc').set_id('ID')
        self.add_table('sentence', ['ID', 'text', 'docID', 'flag', 'comment'],
                       proto=ttl.Sentence, alias='sent').set_id('ID')
        self.add_table('token', ['ID', 'sid', 'widx', 'text', 'lemma', 'pos', 'cfrom', 'cto', 'comment'],
                       proto=ttl.Token).set_id('ID')
        self.add_table('concept', ['ID', 'sid', 'cidx', 'clemma', 'tag', 'flag', 'comment'],
                       proto=ttl.Concept).set_id('ID')
        self.add_table('tag', ['ID', 'sid', 'wid', 'cfrom', 'cto', 'label', 'source', 'tagtype'],
                       proto=ttl.Tag).set_id('ID')
        self.add_table('cwl', ['sid', 'cid', 'wid'], proto=CWLink)

    @with_ctx
    def new_corpus(self, name, title='', ctx=None):
        corpus = Corpus(name=name, title=title)
        newid = ctx.corpus.save(corpus)
        corpus.ID = newid
        return corpus

    @with_ctx
    def new_doc(self, name, corpusID, title='', lang='', ctx=None, **kwargs):
        doc = ttl.Document(name=name, corpusID=corpusID, title=title, lang=lang, **kwargs)
        newid = ctx.doc.save(doc)
        doc.ID = newid
        return doc

    @with_ctx
    def ensure_corpus(self, name, ctx=None, **kwargs):
        corpus = ctx.corpus.select_single('name=?', (name,))
        if corpus is None:
            corpus = self.new_corpus(name, ctx=ctx, **kwargs)
        return corpus

    @with_ctx
    def ensure_doc(self, name, corpus, ctx=None, **kwargs):
        doc = ctx.doc.select_single('name = ?', (name,))
        if doc is None:
            doc = self.new_doc(name=name, corpusID=corpus.ID, ctx=ctx, **kwargs)
        return doc

    @with_ctx
    def save_sent(self, sent_obj, ctx=None):
        # insert sentence
        # save sent obj first
        sent_obj.ID = ctx.sent.save(sent_obj)
        # save sentence's tags
        for tag in sent_obj.tags:
            tag.sid = sent_obj.ID
            tag.wid = None  # ensure that wid is not saved
            tag.ID = ctx.tag.save(tag)
        # save tokens
        for idx, token in enumerate(sent_obj):
            token.sid = sent_obj.ID
            token.widx = idx
            token.ID = ctx.token.save(token)
            # save token's tags
            for tag in token:
                tag.sid = sent_obj.ID
                tag.wid = token.ID
                tag.ID = ctx.tag.save(tag)
        # save concepts
        for idx, concept in enumerate(sent_obj.concepts):
            concept.sid = sent_obj.ID
            concept.ID = ctx.concept.save(concept)
            # save cwl
            for token in concept.tokens:
                cwl = CWLink(sid=sent_obj.ID, cid=concept.ID, wid=token.ID)
                ctx.cwl.save(cwl)
        return sent_obj

    @with_ctx
    def get_sent(self, sentID, ctx=None):
        sent = ctx.sent.by_id(sentID)
        # select tokens
        tokens = ctx.token.select('sid = ?', (sent.ID,))
        tokenmap = {t.ID: t for t in tokens}
        for tk in tokens:
            sent.tokens.append(tk)
        # select all tags
        tags = ctx.tag.select('sid = ?', (sent.ID,))
        for tag in tags:
            if tag.wid is None:
                sent.tags.append(tag)
            elif tag.wid in tokenmap:
                tokenmap[tag.wid].tags.append(tag)
            else:
                getLogger().warning("Orphan tag in sentence #{}: {}".format(sent.ID, tag))
        # select concepts
        concepts = ctx.concept.select('sid = ?', (sent.ID,))
        conceptmap = {c.ID: c for c in concepts}
        for c in concepts:
            sent.add_concept(c)
        # select cwl
        cwlinks = ctx.cwl.select('sid = ?', (sent.ID,))
        for cwl in cwlinks:
            conceptmap[cwl.cid].add_token(tokenmap[cwl.wid])
        return sent

    @with_ctx
    def lexicon(self, limit=None, ctx=None):
        query = 'SELECT text, COUNT(*) FROM token GROUP BY text ORDER BY COUNT(*) DESC'
        params = []
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        return ctx.execute(query, params)

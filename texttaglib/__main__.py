# -*- coding: utf-8 -*-

'''
TTL Tools

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

from chirptext import io as chio
from chirptext.cli import CLIApp, setup_logging

from texttaglib import ttl, TTLSQLite, ttlig

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

setup_logging('logging.json', 'logs')


def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

def get_doc_length(name, ctx):
    query = 'SELECT COUNT(*) FROM sentence WHERE docID = (SELECT ID FROM document WHERE name=?)'
    return ctx.select_scalar(query, (name,))


def make_db(cli, args):
    ''' Convert TTL-TXT to TTL-SQLite '''
    print("Reading document ...")
    ttl_doc = ttl.Document.read_ttl(args.ttl)
    print("Sentences: {}".format(len(ttl_doc)))
    db = TTLSQLite(args.db)
    db_corpus = db.ensure_corpus(name=args.corpus)
    db_doc = db.ensure_doc(name=args.doc if args.doc else ttl_doc.name, corpus=db_corpus)
    if get_doc_length(db_doc.name, ctx=db.ctx()):
        print("Document is not empty, program aborted.")
    else:
        # insert sents
        with db.ctx() as ctx:
            ctx.buckmode()
            ctx.execute('BEGIN;')
            for idx, sent in enumerate(ttl_doc):
                if args.topk and args.topk <= idx:
                    break
                print("Processing sent #{}/{}".format(idx + 1, len(ttl_doc)))
                sent.ID = None
                sent.docID = db_doc.ID
                db.save_sent(sent, ctx=ctx)
            ctx.execute('COMMIT;')
    print("Done!")


def make_ttl(cli, args):
    ''' Convert TTLIG file to TTL format '''
    sc = 0
    ttl_writer = ttl.TxtWriter.from_path(args.output) if args.output else None
    with chio.open(args.ttlig) as infile:
        for sent in ttlig.read_stream_iter(infile):
            sc += 1
            if ttl_writer is not None:
                ttl_sent = sent.to_ttl()
                ttl_writer.write_sent(ttl_sent)
    if ttl_writer is not None:
        print("Output file: {}".format(args.output))
    print("Processed {} sentence(s).".format(sc))


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

def main():
    ''' texttaglib tools '''
    app = CLIApp(desc='Texttaglib Tools', logger=__name__)
    # add tasks
    task = app.add_task('convert', func=make_db)
    task.add_argument('ttl', help='TTL file')
    task.add_argument('db', help='TTL DB file')
    task.add_argument('corpus', help='Corpus name')
    task.add_argument('doc', help='Document name', default=None)
    task.add_argument('-k', '--topk', help='Only select the top k frequent elements', default=None, type=int)

    task = app.add_task('ig', func=make_ttl)
    task.add_argument('ttlig', help='TTLIG file')
    task.add_argument('-o', '--output', help='Output TTL file')
    # run app
    app.run()


if __name__ == "__main__":
    main()

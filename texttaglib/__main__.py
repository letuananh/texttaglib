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

import os
import logging
from lxml import etree

from chirptext import TextReport, FileHelper
from chirptext import io as chio
from chirptext.cli import CLIApp, setup_logging

from texttaglib import ttl, TTLSQLite, ttlig, orgmode

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

setup_logging('logging.json', 'logs')


def getLogger():
    return logging.getLogger(__name__)


FORMAT_TTL = 'ttl'
FORMAT_EXPEX = 'expex'


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


def make_expex_gloss(raw, lines, gloss_tag):
    _tokens = ttlig.tokenize(raw)
    lines.append('\\{} {} //'.format(gloss_tag, ' '.join(_tokens)))
    return len(_tokens)


def process_tig(cli, args):
    ''' Convert TTLIG file to TTL format '''
    if args.format == FORMAT_TTL:
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
    elif args.format == FORMAT_EXPEX:
        sc = 0
        output = TextReport(args.output)
        with chio.open(args.ttlig) as infile:
            for idx, sent in enumerate(ttlig.read_stream_iter(infile)):
                sc += 1
                lines = []
                sent_ident = sent.ident if sent.ident else idx + 1
                lines.append('\\ex \\label{{{}}}'.format(sent_ident))
                lines.append('\\begingl[aboveglftskip=0pt]')
                tags = ['gla', 'glb', 'glc']
                # process tokens and gloss
                glosses = []
                lengths = []
                if sent.tokens:
                    lengths.append(make_expex_gloss(sent.tokens, glosses, tags.pop(0)))
                if sent.morphtrans:
                    lengths.append(make_expex_gloss(sent.morphtrans, glosses, tags.pop(0)))
                if sent.morphgloss:
                    lengths.append(make_expex_gloss(sent.morphgloss, glosses, tags.pop(0)))
                if sent.concept:
                    if tags:
                        lengths.append(make_expex_gloss(sent.concept, glosses, tags.pop(0)))
                    else:
                        cli.logger.warning("There are too many gloss lines in sentence {}. {}".format(sent_ident, sent.text))
                # ensure that number of tokens are the same
                if len(lengths) > 1:
                    for line_len in lengths[1:]:
                        if line_len != lengths[0]:
                            cli.logger.warning("Inconsistent tokens and morphgloss for sentence {}. {} ({} v.s {})".format(sent_ident, sent.text, line_len, lengths[0]))
                            break
                lines.extend(glosses)
                lines.append('\\glft {}//'.format(sent.text))
                lines.append('\\endgl')
                lines.append('\\xe')
                output.print('\n'.join(lines))
                output.print()
                output.print()
                output.print()
    else:
        print("Format {} is not supported".format(args.format))


def jp_line_proc(line, iglines):
    igrow = ttlig.text_to_igrow(line.replace('\u3000', ' ').strip())
    iglines.append(igrow.text)
    iglines.append(igrow.tokens)
    iglines.append("")


def convert_org_to_tig(inpath, outpath):
    title, meta, lines = orgmode.read(inpath)
    meta.append(("Lines", "text tokens"))
    out = orgmode.org_to_ttlig(title, meta, lines, jp_line_proc)
    output = TextReport(outpath)
    for line in out:
        output.print(line)


def org_to_ttlig(cli, args):
    ''' Convert ORG file to TTLIG format '''
    if args.orgfile:
        # single file mode
        convert_org_to_tig(args.orgfile, args.output)
    elif args.orgdir:
        if not args.output:
            print("Output directory is required for batch mode")
            exit()
        # make output directory
        if not os.path.exists(args.output):
            print("Make directory: {}".format(args.output))
            os.makedirs(args.output)
        else:
            print("Output directory: {}".format(args.output))
        filenames = FileHelper.get_child_files(args.orgdir)
        for filename in filenames:
            infile = os.path.join(args.orgdir, filename)
            outfile = os.path.join(args.output, FileHelper.replace_ext(filename, 'tig'))
            if os.path.exists(outfile):
                print("File {} exists. SKIPPED".format(outfile))
            else:
                print("Generating: {} => {}".format(infile, outfile))
                convert_org_to_tig(infile, outfile)
    print("Done")


def make_text(sent, delimiter=' '):
    frags = []
    if sent.tokens:
        for tk in sent:
            furi = tk.find('furi', default=None)
            if furi:
                frags.append(ttlig.make_ruby_html(furi.label))
            else:
                frags.append(tk.text)
    html_text = delimiter.join(frags) if frags else sent.text
    return "<text>{}</text>".format(html_text)


def make_html(cli, args):
    ''' Convert TTL to HTML '''
    print("Reading document ...")
    ttl_doc = ttl.Document.read_ttl(args.ttl)
    output = TextReport(args.output)
    doc_node = etree.Element('doc')
    for sent in ttl_doc:
        sent_node = etree.SubElement(doc_node, 'sent')
        text_node = etree.XML(make_text(sent, delimiter=args.delimiter))
        sent_node.append(text_node)
        if sent.get_tag('translation'):
            etree.SubElement(sent_node, 'br')
            trans_node = etree.SubElement(sent_node, 'trans')
            trans_node.text = sent.get_tag('translation').label
        etree.SubElement(sent_node, 'br')
        etree.SubElement(sent_node, 'br')
    output.write(etree.tostring(doc_node, encoding='unicode', pretty_print=not args.compact))


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

    task = app.add_task('ig', func=process_tig)
    task.add_argument('ttlig', help='TTLIG file')
    task.add_argument('-o', '--output', help='Output TTL file')
    task.add_argument('-f', '--format', help='Output format', choices=[FORMAT_EXPEX, FORMAT_TTL], default=FORMAT_TTL)

    task = app.add_task('org', func=org_to_ttlig)
    task.add_argument('-f', '--orgfile', help='ORG file')
    task.add_argument('-d', '--orgdir', help='ORG directory (batch mode)')
    task.add_argument('-o', '--output', help='Output TTL file or directory')

    task = app.add_task('html', func=make_html)
    task.add_argument('ttl', help='TTL file')
    task.add_argument('-o', '--output', help='path to output HTML file')
    task.add_argument('-c', '--compact', help='Do not use pretty print', action='store_true')
    task.add_argument('-d', '--delimiter', help='Token delimiter', default=' ')

    # run app
    app.run()


if __name__ == "__main__":
    main()

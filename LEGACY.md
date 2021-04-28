# texttaglib

[![ReadTheDocs Badge](https://readthedocs.org/projects/texttaglib/badge/?version=latest&style=plastic)](https://texttaglib.readthedocs.io/)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/letuananh/texttaglib.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/texttaglib/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/letuananh/texttaglib.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/texttaglib/context:python)

## Warning

⚠️ THIS REPOSITORY IS ARCHIVED. ALL FUTURE DEVELOPMENT WILL BE ON [speach](https://github.com/neocl/speach) LIBRARY ⚠️

Migration from `texttaglib` to `speach` should be trivial

```python
# just change import statements from something like
from texttaglib import elan
# to 
from speach import elan
```

Installation

```bash
# change
pip install texttaglib 
# into
pip install speach
```

For more information, please visit: https://github.com/neocl/speach

## Legacy

texttaglib is a Python library for managing and annotating text corpuses in different formats.

Main functions are:

- Multiple storage formats (text files, JSON files, SQLite databases)
- TTLIG - A human-friendly intelinear gloss format for linguistic documentation 
- Manipuling transcription files directly in ELAN Annotation Format (eaf)

## Useful Links

- texttaglib documentation: https://texttaglib.readthedocs.io/
- texttaglib on PyPI: https://pypi.org/project/texttaglib/
- Soure code: https://github.com/letuananh/texttaglib/

## Installation

texttaglib is availble on PyPI.

```bash
pip install texttaglib
# or more explicit
python3 -m pip install texttaglib
```

## Basic usage

```python
>>> from texttaglib import ttl
>>> doc = ttl.Document('mydoc')
>>> sent = doc.new_sent("I am a sentence.")
>>> sent
#1: I am a sentence.
>>> sent.ID
1
>>> sent.text
'I am a sentence.'
>>> sent.import_tokens(["I", "am", "a", "sentence", "."])
>>> >>> sent.tokens
[`I`<0:1>, `am`<2:4>, `a`<5:6>, `sentence`<7:15>, `.`<15:16>]
>>> doc.write_ttl()
```

The script above will generate this corpus

```
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_concepts.txt
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_links.txt
-rw-rw-r--.  1 tuananh tuananh      20  3月 29 13:10 mydoc_sents.txt
-rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_tags.txt
-rw-rw-r--.  1 tuananh tuananh      58  3月 29 13:10 mydoc_tokens.txt
```

## ELAN support

texttaglib library contains a command line tool for converting EAF files into CSV.

```bash
python -m texttaglib eaf2csv input_elan_file.eaf -o output_file_name.csv
```

For more complex analyses, texttaglib Python scripts can be used to extract metadata and annotations from ELAN transcripts, for example:

``` python
from texttaglib.elan import parse_eaf_stream

# Test ELAN reader function in texttaglib
with open('./data/test.eaf') as eaf_stream:
    elan = parse_eaf_stream(eaf_stream)

# accessing metadata
print(f"Author: {elan.author} | Date: {elan.date} | Format: {elan.fileformat} | Version: {elan.version}")
print(f"Media file: {elan.media_file}")
print(f"Time units: {elan.time_units}")
print(f"Media URL: {elan.media_url} | MIME type: {elan.mime_type}")
print(f"Media relative URL: {elan.relative_media_url}")

# accessing tiers & annotations
for tier in elan.tiers():
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    for ann in tier.annotations:
        print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")
```

## SQLite support

TTL data can be stored in a SQLite database for better corpus analysis.
Sample code will be added soon.

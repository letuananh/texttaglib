Python library for managing and annotating textual corpus using TextTagLib (TTL) format

# Installation

texttaglib is availble on PyPI.
```bash
pip install texttaglib
# or more explicit
python3 -m pip install texttaglib
```

# Basic usage
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

# ELAN support
TTL can extract metadata and annotations from ELAN transcripts using Python.
``` python
from texttaglib.elan import parse_eaf_stream

# Test ELAN reader function in texttaglib
with open('./data/test.eaf') as eaf_stream:
    elan = parse_eaf_stream(eaf_stream)

# accessing metadata
print("Author: {} | Date: {} | Format: {} | Version: {}".format(elan.author, elan.date, elan.fileformat, elan.version))
print("Media file: {}".format(elan.media_file))
print("Time units: {}".format(elan.time_units))
print("Media URL: {} | MIME type: {}".format(elan.media_url, elan.mime_type))
print("Media relative URL: {}".format(elan.relative_media_url))

# accessing tiers & annotations
for tier in elan.tiers():
    print("{} | Participant: {} | Type: {}".format(tier.ID, tier.participant, tier.type_ref))
    for anno in tier.annotations:
        print("{}. [{} -- {}] {}".format(anno.ID.rjust(4, ' '), anno.from_ts.ts, anno.to_ts.ts, anno.value))
```

# SQLite support
TTL data can be stored in a SQLite database for better corpus analysis.
Sample code will be added soon.

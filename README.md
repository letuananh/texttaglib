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

# SQLite support
TTL data can be stored in a SQLite database for better corpus analysis.
Sample code will be added soon.

.. texttaglib documentation master file, created by
   sphinx-quickstart on Mon Mar 22 10:49:52 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

texttaglib's documentation!
===========================

.. warning::
    ⚠️ THIS PROJECT HAS BEEN RENAMED AND ARCHIVED. ALL FUTURE DEVELOPMENT WILL BE ON
    `speach <https://pypi.org/project/speach/>`__ LIBRARY ⚠️

Migration to speach
-------------------
    
    Migration from ``texttaglib`` to `speach <https://speach.readthedocs.io/>`_ should be trivial


.. code:: python

    # just change import statements from something like
    from texttaglib import elan
    # to the new package name
    from speach import elan

Installation

.. code:: bash

    # change
    pip install texttaglib 
    # into
    pip install speach

-  For more information, please visit: https://speach.readthedocs.io/

(Legacy) Introduction
---------------------

texttaglib is a Python library for managing and annotating text corpuses in different formats.

.. image:: https://readthedocs.org/projects/texttaglib/badge/?version=latest&style=plastic
   :target: https://texttaglib.readthedocs.io/
.. image:: https://img.shields.io/lgtm/alerts/g/letuananh/texttaglib.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/texttaglib/alerts/
.. image:: https://img.shields.io/lgtm/grade/python/g/letuananh/texttaglib.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/texttaglib/context:python

Main functions are:

-  Multiple storage formats (text files, JSON files, SQLite databases)
-  TTLIG - A human-friendly intelinear gloss format for linguistic
   documentation
-  Manipuling transcription files directly in ELAN Annotation Format
   (eaf)

Installation
------------

texttaglib is availble on PyPI.

.. code:: bash

   pip install texttaglib

Basic usage
-----------

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

The script above will generate this corpus

::

   -rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_concepts.txt
   -rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_links.txt
   -rw-rw-r--.  1 tuananh tuananh      20  3月 29 13:10 mydoc_sents.txt
   -rw-rw-r--.  1 tuananh tuananh       0  3月 29 13:10 mydoc_tags.txt
   -rw-rw-r--.  1 tuananh tuananh      58  3月 29 13:10 mydoc_tokens.txt

ELAN support
------------

texttaglib library contains a command line tool for converting EAF files
into CSV.

.. code:: bash

   python -m texttaglib eaf2csv input_elan_file.eaf -o output_file_name.csv

For more complex analyses, texttaglib Python scripts can be used to
extract metadata and annotations from ELAN transcripts, for example:

.. code:: python

   from texttaglib import elan

   # Test ELAN reader function in texttaglib
   eaf = elan.open_eaf('./data/test.eaf')

   # accessing metadata
   print(f"Author: {eaf.author} | Date: {eaf.date} | Format: {eaf.fileformat} | Version: {eaf.version}")
   print(f"Media file: {eaf.media_file}")
   print(f"Time units: {eaf.time_units}")
   print(f"Media URL: {eaf.media_url} | MIME type: {eaf.mime_type}")
   print(f"Media relative URL: {eaf.relative_media_url}")

   # accessing tiers & annotations
   for tier in eaf.tiers():
       print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
       for ann in tier.annotations:
           print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")

SQLite support
--------------

TTL data can be stored in a SQLite database for better corpus analysis.
Sample code will be added soon.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorials
   recipes
   api

Useful Links
------------

- pyInkscape documentation: https://texttaglib.readthedocs.io/
- pyInkscape on PyPI: https://pypi.org/project/texttaglib/
- Soure code: https://github.com/letuananh/texttaglib/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

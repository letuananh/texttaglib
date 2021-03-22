texttaglib APIs
===============

An overview of texttaglib modules.

.. module:: texttaglib

ELAN supports
-------------

texttaglib supports reading and manipulating multi-tier transcriptions from ELAN directly.
            
.. automodule:: texttaglib.elan
   :members: open_eaf, parse_eaf_stream

.. autoclass:: ELANDoc
   :members:

.. autoclass:: ELANTier
   :members:
   :member-order: groupwise

TTL Interlinear Gloss Format
----------------------------

TTLIG is a human friendly interlinear gloss format that can be edited using any text editor.
            
.. module:: texttaglib.ttlig

TTL SQLite
----------

TTL supports SQLite storage format to manage large scale corpuses.
            
.. module:: texttaglib.sqlite


Common Recipes
==============

Here are code snippets for common usecases of texttaglib

Open an ELAN file
-----------------

.. code-block:: python

   with open('./data/test.eaf') as eaf_stream:
       elan = parse_eaf_stream(eaf_stream)

Accessing tiers & annotations
-----------------------------

.. code-block:: python

    for tier in elan.tiers():
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        for ann in tier.annotations:
            print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")

Accessing nested tiers in ELAN
------------------------------

.. code-block:: python

    with open('./data/test_nested.eaf') as eaf_stream:
        elan2 = parse_eaf_stream(eaf_stream)
    # accessing nested tiers
    for tier in elan2.roots:
        print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
        print(f"  -- {ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")    
        for child_tier in tier.children:
            print(f"    | {child_tier.ID} | Participant: {child_tier.participant} | Type: {child_tier.type_ref}")
            for ann in child_tier.annotations:
                print(f"    |- {ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")
         
Converting ELAN files to CSV
----------------------------

texttaglib includes a command line tool to convert an EAF file into CSV.

.. code-block:: bash

   python -m texttaglib eaf2csv my_transcript.eaf -o my_transcript.csv

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

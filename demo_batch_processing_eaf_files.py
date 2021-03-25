from pathlib import Path
from texttaglib.elan import open_eaf


TRANSCRIPT_FOLDER = 'data/transcript/'
csv_data = []
for child_file in Path(TRANSCRIPT_FOLDER).iterdir():
    if child_file.suffix.endswith('.eaf'):
        print(child_file.name)
        c = 0
        elan2 = open_eaf(child_file)
        for tier in elan2.roots:
            if tier.type_ref == 'Utterance':
                print(f"  | {tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
                for ann in tier.annotations:
                    if 'BABYNAME' in ann.value:
                        c += 1
                        print(f"  | -- {tier.ID} --> {tier.participant}: {ann.value}")
        print(c)
        csv_data.append((child_file.name, c))

for fn, c in csv_data:
    print(f"{fn}\t{c}")

# -*- coding: utf-8 -*-

'''
ELAN module for manipulating ELAN transcript files (*.eaf, *.pfsx)

Latest version can be found at https://github.com/letuananh/texttaglib

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2020, Le Tuan Anh <tuananh.ke@gmail.com>
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
from collections import OrderedDict
from collections import defaultdict as dd
import xml.etree.ElementTree as ET

from chirptext import DataObject

from .vtt import sec2ts, ts2sec


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class TimeSlot():
    def __init__(self, ID, value=None):
        """
        An ELAN timestamp (with ID)
        """
        self.ID = ID
        self.value = value

    @property
    def ts(self):
        return sec2ts(self.sec) if self.value is not None else None

    @property
    def sec(self):
        return self.value / 1000 if self.value is not None else None

    def __lt__(self, other):
        return self.value < other.value if isinstance(other, TimeSlot) else self.value < other

    def __gt__(self, other):
        return self.value > other.value if isinstance(other, TimeSlot) else self.value > other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        return self.value == other.value if isinstance(other, TimeSlot) else self.value == other

    def __add__(self, other):
        return self.value + other.value if isinstance(other, TimeSlot) else self.value + other

    def __sub__(self, other):
        return self.value - other.value if isinstance(other, TimeSlot) else self.value - other

    def __hash__(self):
        return id(self)

    def __str__(self):
        val = self.ts
        return val if val else self.ID

    @staticmethod
    def from_node(node):
        slotID = node.get('TIME_SLOT_ID')
        value = node.get('TIME_VALUE')
        if value is not None:
            return TimeSlot(slotID, int(node.get('TIME_VALUE')))
        else:
            return TimeSlot(slotID)

    @staticmethod
    def from_ts(ts, ID=None):
        value = ts2sec(ts) * 1000
        return TimeSlot(ID=ID, value=value)


class ELANAnnotation(DataObject):
    def __init__(self, ID, value, cve_ref=None, **kwargs):
        """
        An ELAN abstract annotation
        """
        super().__init__(**kwargs)
        self.ID = ID
        self.value = value
        self.cve_ref = cve_ref

    def __repr__(self):
        return "[{}]".format(self.value)

    def __str__(self):
        return str(self.value)


class ELANTimeAnnotation(ELANAnnotation):
    def __init__(self, ID, from_ts, to_ts, value, **kwargs):
        """
        An ELAN time-alignable annotation
        """
        super().__init__(ID, value, **kwargs)
        self.from_ts = from_ts
        self.to_ts = to_ts

    @property
    def duration(self):
        return self.to_ts.sec - self.from_ts.sec

    def overlap(self, other):
        ''' Calculate overlap score between two time annotations
        Score = 0 means adjacent, score > 0 means overlapped, score < 0 means no overlap (the distance between the two)
        '''
        return min(self.to_ts, other.to_ts) - max(self.from_ts, other.from_ts)

    def __repr__(self):
        return '[{} -- {}] {}'.format(self.from_ts, self.to_ts, self.value)

    def __str__(self):
        return str(self.value)


class ELANRefAnnotation(ELANAnnotation):
    def __init__(self, ID, ref, previous, value, **kwargs):
        """
        An ELAN ref annotation (not time alignable)
        """
        super().__init__(ID, value, **kwargs)
        self.ref = ref  # ANNOTATION_REF
        self.previous = previous  # PREVIOUS_ANNOTATION


class ELANTier(DataObject):

    NONE = "None"
    TIME_SUB = "Time_Subdivision"
    SYM_SUB = "Symbolic_Subdivision"
    INCL = "Included_In"
    SYM_ASSOC = "Symbolic_Association"

    def __init__(self, type_ref, participant, ID, doc=None, default_locale=None, parent_ref=None, **kwargs):
        """
        ELAN Tier Model which contains annotation objects
        """
        super().__init__(**kwargs)
        self.type_ref = type_ref
        self.linguistic_type = None
        self.participant = participant if participant else ''
        self.ID = ID
        self.default_locale = default_locale
        self.parent_ref = parent_ref
        self.parent = None
        self.doc = doc
        self.children = []
        self.annotations = []

    def __getitem__(self, key):
        return self.annotations[key]

    def __iter__(self):
        return iter(self.annotations)

    def get_child(self, ID):
        ''' Get a child tier by ID, return None if nothing is found '''
        for child in self.children:
            if child.ID == ID:
                return child
        return None

    def filter(self, from_ts=None, to_ts=None):
        ''' Filter utterances by from_ts or to_ts or both
        If this tier is not a time-based tier everything will be returned
        '''
        for ann in self.annotations:
            if from_ts is not None and ann.from_ts is not None and ann.from_ts < from_ts:
                continue
            elif to_ts is not None and ann.to_ts is not None and ann.from_ts > to_ts:
                continue
            else:
                yield ann

    def __len__(self):
        return len(self.annotations)

    def __repr__(self):
        return 'Tier(ID={})'.format(self.ID)

    def __str__(self):
        return 'Tier(ID={}/type={})'.format(self.ID, self.type_ref)

    def add_alignable_annotation_xml(self, alignable):
        ann_id = alignable.get('ANNOTATION_ID')
        from_ts_id = alignable.get('TIME_SLOT_REF1')
        cve_ref = alignable.get('CVE_REF')  # controlled vocab ref
        if from_ts_id not in self.doc.time_order:
            raise ValueError("Time slot ID not found ({})".format(from_ts_id))
        else:
            from_ts = self.doc.time_order[from_ts_id]
        to_ts_id = alignable.get('TIME_SLOT_REF2')
        if to_ts_id not in self.doc.time_order:
            raise ValueError("Time slot ID not found ({})".format(to_ts_id))
        else:
            to_ts = self.doc.time_order[to_ts_id]
        # [TODO] ensure that from_ts < to_ts
        value_node = alignable.find('ANNOTATION_VALUE')
        if value_node is None:
            raise ValueError("ALIGNABLE_ANNOTATION node must contain an ANNOTATION_VALUE node")
        else:
            value = value_node.text if value_node.text else ''
            anno = ELANTimeAnnotation(ann_id, from_ts, to_ts, value, cve_ref=cve_ref)
            self.annotations.append(anno)
            return anno

    def add_ref_annotation_xml(self, ref_node):
        ann_id = ref_node.get('ANNOTATION_ID')
        ref = ref_node.get('ANNOTATION_REF')
        previous = ref_node.get('PREVIOUS_ANNOTATION')
        cve_ref = ref_node.get('CVE_REF')  # controlled vocab ref
        value_node = ref_node.find('ANNOTATION_VALUE')
        if value_node is None:
            raise ValueError("REF_ANNOTATION node must contain an ANNOTATION_VALUE node")
        else:
            value = value_node.text if value_node.text else ''
            anno = ELANRefAnnotation(ann_id, ref, previous, value, cve_ref=cve_ref)
            self.annotations.append(anno)
            return anno

    def add_annotation_xml(self, annotation_node):
        ''' Create an annotation from a node '''
        alignable = annotation_node.find('ALIGNABLE_ANNOTATION')
        if alignable is not None:
            self.add_alignable_annotation_xml(alignable)
        else:
            ref_ann_node = annotation_node.find('REF_ANNOTATION')
            if ref_ann_node is not None:
                self.add_ref_annotation_xml(ref_ann_node)
            else:
                raise ValueError("ANNOTATION node must not be empty")


class LinguisticType(DataObject):
    def __init__(self, xml_node=None):
        """
        Linguistic Tier Type
        """
        data = {k.lower(): v for k, v in xml_node.attrib.items()} if xml_node is not None else {}
        super().__init__(**data)
        self.vocab = None
        self.tiers = []


class ELANCVEntry(DataObject):
    def __init__(self, ID, lang_ref, value, description=None):
        """

        """
        self.ID = ID
        self.lang_ref = lang_ref
        self.value = value
        self.description = description

    def __repr__(self):
        return '[{}{}]'.format(self.value, " | {}".format(self.description) if self.description else "")

    def __str__(self):
        return self.value


class ELANVocab(DataObject):
    ''' ELAN Controlled Vocabulary '''
    def __init__(self, ID, description, lang_ref, entries=None, **kwargs):
        """

        """
        self.ID = ID
        self.description = description
        self.lang_ref = lang_ref
        self.entries = list(entries) if entries else []
        self.entries_map = {e.ID: e for e in self.entries}
        self.tiers = []

    def __getitem__(self, key):
        return self.entries_map[key]

    def __iter__(self):
        return iter(self.entries)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'Vocab({} | count={})'.format(self.ID, len(self.entries))

    @staticmethod
    def from_xml(node):
        CVID = node.get('CV_ID')
        description = ""
        lang_ref = ""
        entries = []
        for child in node:
            if child.tag == 'DESCRIPTION':
                description = child.text
                lang_ref = child.get('LANG_REF')
            elif child.tag == 'CV_ENTRY_ML':
                entryID = child.get('CVE_ID')
                entry_value_node = child.find('CVE_VALUE')
                entry_lang_ref = entry_value_node.get('LANG_REF')
                entry_value = entry_value_node.text
                entry_description = entry_value_node.get('DESCRIPTION')
                cv_entry = ELANCVEntry(entryID, entry_lang_ref, entry_value, description=entry_description)
                entries.append(cv_entry)
        return ELANVocab(CVID, description, lang_ref, entries=entries)


class ELANContraint(DataObject):
    def __init__(self, xml_node=None):
        super().__init__()
        if xml_node is not None:
            self.description = xml_node.get('DESCRIPTION')
            self.stereotype = xml_node.get('STEREOTYPE')


class ELANDoc(DataObject):
    def __init__(self, **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.properties = OrderedDict()
        self.time_order = OrderedDict()
        self.tiers_map = OrderedDict()
        self.linguistic_types = []
        self.constraints = []
        self.vocabs = []
        self.roots = []

    def get_linguistic_type(self, type_id):
        ''' Get linguistic type by ID. Return None if can not be found '''
        for lingtype in self.linguistic_types:
            if lingtype.linguistic_type_id == type_id:
                return lingtype
        return None

    def get_vocab(self, vocab_id):
        ''' Get controlled vocab list by ID '''
        for vocab in self.vocabs:
            if vocab.ID == vocab_id:
                return vocab
        return None

    def get_participant_map(self):
        ''' Map participants to tiers
        Return a map from participant name to a list of corresponding tiers
        '''
        par_map = dd(list)
        for t in self.tiers():
            par_map[t.participant].append(t)
        return par_map

    def __iter__(self):
        return iter(self.tiers_map.values())

    def tiers(self):
        return self.tiers_map.values()

    def update_info_xml(self, node):
        self.author = node.get('AUTHOR')
        self.date = node.get('DATE')
        self.fileformat = node.get('FORMAT')
        self.version = node.get('VERSION')

    def update_header_xml(self, node):
        ''' Read ELAN doc information from HEADER node '''
        self.media_file = node.get('MEDIA_FILE')
        self.time_units = node.get('TIME_UNITS')
        # extract media information
        media_node = node.find('MEDIA_DESCRIPTOR')
        if media_node is not None:
            self.media_url = media_node.get('MEDIA_URL')
            self.mime_type = media_node.get('MIME_TYPE')
            self.relative_media_url = media_node.get('RELATIVE_MEDIA_URL')
        # extract properties
        for prop_node in node.findall('PROPERTY'):
            self.properties[prop_node.get('NAME')] = prop_node.text

    def add_tier_xml(self, tier_node):
        type_ref = tier_node.get('LINGUISTIC_TYPE_REF')
        participant = tier_node.get('PARTICIPANT')
        tier_id = tier_node.get('TIER_ID')
        parent_ref = tier_node.get('PARENT_REF')
        default_locale = tier_node.get('DEFAULT_LOCALE')
        tier = ELANTier(type_ref, participant, tier_id, doc=self, default_locale=default_locale, parent_ref=parent_ref)
        if tier_id in self.tiers_map:
            raise ValueError("Duplicated tier ID ({})".format(tier_id))
        self.tiers_map[tier_id] = tier
        return tier

    def add_timeslot_xml(self, timeslot_node):
        timeslot = TimeSlot.from_node(timeslot_node)
        self.time_order[timeslot.ID] = timeslot

    def to_csv_rows(self):
        rows = []
        for tier in self.tiers():
            for anno in tier.annotations:
                _from_ts = f"{anno.from_ts.sec:.3f}" if anno.from_ts else None
                _to_ts = f"{anno.to_ts.sec:.3f}" if anno.to_ts else None
                _duration = f"{anno.duration:.3f}" if anno.duration else None
                rows.append((tier.ID, tier.participant, _from_ts, _to_ts, _duration, anno.value))
        return rows


def __resolve(elan_doc):
    ''' Ensure that everything is linked together (e.g. tiers, vocabs, etc.) '''
    # link linguistic_types -> vocabs
    for lingtype in elan_doc.linguistic_types:
        if lingtype.controlled_vocabulary_ref:
            lingtype.vocab = elan_doc.get_vocab(lingtype.controlled_vocabulary_ref)
    # resolves tiers' roots, parents, and type
    elan_doc.roots = []
    # link tier to parents
    for tier in elan_doc.tiers():
        lingtype = elan_doc.get_linguistic_type(tier.type_ref)
        tier.linguistic_type = lingtype
        lingtype.tiers.append(tier)  # type -> tiers
        if lingtype.vocab:
            lingtype.vocab.tiers.append(tier)  # vocab -> tiers
        if tier.parent_ref is not None:
            tier.parent = elan_doc.tiers_map[tier.parent_ref]
            elan_doc.tiers_map[tier.parent_ref].children.append(tier)
        else:
            elan_doc.roots.append(tier)


def parse_eaf_stream(eaf_stream):
    elan_doc = ELANDoc()
    current_tier = None
    for event, elem in ET.iterparse(eaf_stream, events=('start', 'end')):
        if event == 'start':
            if elem.tag == 'ANNOTATION_DOCUMENT':
                elan_doc.update_info_xml(elem)
            elif elem.tag == 'TIER':
                current_tier = elan_doc.add_tier_xml(elem)
        elif event == 'end':
            if elem.tag == 'HEADER':
                elan_doc.update_header_xml(elem)
                elem.clear()  # no need to keep header node in memory
            elif elem.tag == 'TIME_SLOT':
                elan_doc.add_timeslot_xml(elem)
                elem.clear()
            elif elem.tag == 'ANNOTATION':
                current_tier.add_annotation_xml(elem)
                elem.clear()
            elif elem.tag == 'LINGUISTIC_TYPE':
                elan_doc.linguistic_types.append(LinguisticType(elem))
                elem.clear()
            elif elem.tag == 'CONSTRAINT':
                elan_doc.constraints.append(ELANContraint(elem))
                elem.clear()
            elif elem.tag == 'CONTROLLED_VOCABULARY':
                elan_doc.vocabs.append(ELANVocab.from_xml(elem))
                elem.clear()
    __resolve(elan_doc)  # link parts together
    return elan_doc

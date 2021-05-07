# -*- coding: utf-8 -*-

'''
ELAN module for manipulating ELAN transcript files (\*.eaf, \*.pfsx)
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
#
# Latest version can be found at https://github.com/letuananh/texttaglib

########################################################################

import logging
from collections import OrderedDict
from collections import defaultdict as dd
from typing import List, Tuple
import xml.etree.ElementTree as ET

from .chirptext import DataObject
from .chirptext import chio

from .vtt import sec2ts, ts2sec


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

CSVRow = List[str]
CSVTable = List[CSVRow]


class TimeSlot():
    def __init__(self, ID, value=None):
        """ An ELAN timestamp (with ID)
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
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return False
        return self.value < other.value if isinstance(other, TimeSlot) else self.value < other

    def __eq__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return False
        return self.value == other.value if isinstance(other, TimeSlot) else self.value == other

    def __gt__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return True
        return self.value > other.value if isinstance(other, TimeSlot) else self.value > other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

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
    """ An ELAN abstract annotation (for both alignable and non-alignable annotations)
    """

    def __init__(self, ID, value, cve_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.ID = ID
        self.value = value
        self.cve_ref = cve_ref

    def __repr__(self):
        return "[{}]".format(self.value)

    def __str__(self):
        return str(self.value)


class ELANTimeAnnotation(ELANAnnotation):
    """ An ELAN time-alignable annotation
    """
    def __init__(self, ID, from_ts, to_ts, value, **kwargs):
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
    """ An ELAN ref annotation (not time alignable)
    """

    def __init__(self, ID, ref, previous, value, **kwargs):
        super().__init__(ID, value, **kwargs)
        self.ref = ref  # ANNOTATION_REF
        self.previous = previous  # PREVIOUS_ANNOTATION


class LinguisticType(DataObject):
    def __init__(self, xml_node=None):
        """
        Linguistic Tier Type
        """
        data = {k.lower(): v for k, v in xml_node.attrib.items()} if xml_node is not None else {}
        if "time_alignable" in data:
            data["time_alignable"] = data["time_alignable"] == "true"
        super().__init__(**data)
        self.vocab = None
        self.tiers = []

    @property
    def ID(self):
        return self.linguistic_type_id

    def __repr__(self):
        return f"LinguisticType(ID={repr(self.ID)}, constraints={repr(self.constraints)}"


class ELANTier(DataObject):
    """ Represents an ELAN annotation tier """

    NONE = "None"
    TIME_SUB = "Time_Subdivision"
    SYM_SUB = "Symbolic_Subdivision"
    INCL = "Included_In"
    SYM_ASSOC = "Symbolic_Association"

    def __init__(self, type_ref_id, participant, ID, doc=None, default_locale=None, parent_ref=None, **kwargs):
        """
        ELAN Tier Model which contains annotation objects
        """
        super().__init__(**kwargs)
        self.__type_ref = None
        self.__type_ref_id = type_ref_id
        self.participant = participant if participant else ''
        self.ID = ID
        self.default_locale = default_locale
        self.parent_ref = parent_ref
        self.parent = None
        self.doc = doc
        self.children = []
        self.annotations = []

    @property
    def time_alignable(self):
        """ Check if this tier contains time alignable annotations """
        return self.linguistic_type and self.linguistic_type.time_alignable

    @property
    def linguistic_type(self) -> LinguisticType:
        """ Linguistic type object of this Tier """
        return self.__type_ref

    def _set_type_ref(self, type_ref_object):
        """ [Internal function] Update type_ref object of this Tier """
        self.__type_ref = type_ref_object

    @property
    def _type_ref_id(self):
        return self.__type_ref_id

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
        return f'Tier(ID={repr(self.ID)}),type={repr(self.linguistic_type)})'.format(self.ID, self.linguistic_type)

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

    def _add_annotation_xml(self, annotation_node) -> ELANAnnotation:
        """ [Internal function] Create an annotation from a node
        
        General users should not use this function.
        """
        alignable = annotation_node.find('ALIGNABLE_ANNOTATION')
        if alignable is not None:
            return self.add_alignable_annotation_xml(alignable)
        else:
            ref_ann_node = annotation_node.find('REF_ANNOTATION')
            if ref_ann_node is not None:
                return self.add_ref_annotation_xml(ref_ann_node)
            else:
                raise ValueError("ANNOTATION node must not be empty")


class ELANCVEntry(DataObject):

    ''' A controlled vocabulary entry '''
    
    def __init__(self, ID, lang_ref, value, description=None, **kwargs):
        super().__init__(**kwargs)
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
        super().__init__(**kwargs)
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
    """ ELAN Tier Constraints """

    def __init__(self, xml_node=None):
        super().__init__()
        if xml_node is not None:
            self.description = xml_node.get('DESCRIPTION')
            self.stereotype = xml_node.get('STEREOTYPE')


TierTuple = Tuple[ELANTier]
LinguisticTypeTuple= Tuple[LinguisticType]
ConstraintTuple = Tuple[ELANContraint]
VocabTuple = Tuple[ELANVocab]


class ELANDoc(DataObject):

    ''' This class represents an ELAN file (\*.eaf)
    '''
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.properties = OrderedDict()
        self.time_order = OrderedDict()
        self.__tiers_map = OrderedDict()  # internal - map tierIDs to tier objects
        self.__linguistic_types = []
        self.__constraints = []
        self.__vocabs = []
        self.__roots = []

    @property
    def roots(self) -> TierTuple:
        """ All root-level tiers in this ELAN doc """
        return tuple(self.__roots)

    @property
    def vocabs(self) -> VocabTuple:
        """ A tuple of all existing controlled vocabulary objects in this ELAN file """
        return tuple(self.__vocabs)

    @property
    def constraints(self) -> ConstraintTuple:
        """ A tuple of all existing constraints in this ELAN file """
        return tuple(self.__constraints)

    @property
    def linguistic_types(self) -> LinguisticTypeTuple:
        """ A tuple of all existing linguistic types in this ELAN file """
        return tuple(self.__linguistic_types)

    def get_linguistic_type(self, type_id):
        ''' Get linguistic type by ID. Return None if can not be found '''
        for lingtype in self.__linguistic_types:
            if lingtype.linguistic_type_id == type_id:
                return lingtype
        return None

    def get_vocab(self, vocab_id):
        ''' Get controlled vocab list by ID '''
        for vocab in self.__vocabs:
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

    def __getitem__(self, tierID):
        ''' Find a tier object using tierID '''
        return self.__tiers_map[tierID]
    
    def __iter__(self):
        """ Iterate through all tiers in this ELAN file """
        return iter(self.__tiers_map.values())

    def tiers(self) -> TierTuple:
        """ Collect all existing Tier in this ELAN file 
        """
        return tuple(self.__tiers_map.values())

    def _update_info_xml(self, node):
        ''' [Internal function] Update ELAN file metadata from an XML node 
        
        General users should not use this function.
        '''
        self.author = node.get('AUTHOR')
        self.date = node.get('DATE')
        self.fileformat = node.get('FORMAT')
        self.version = node.get('VERSION')

    def _update_header_xml(self, node):
        ''' [Internal function] Read ELAN doc information from a HEADER XML node 

        General users should not use this function.
        '''
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

    def _add_tier_xml(self, tier_node) -> ELANTier:
        ''' [Internal function] Parse a TIER XML node, create an ELANTier object and link it to this ELANDoc

        General users should not use this function.
        '''
        type_ref = tier_node.get('LINGUISTIC_TYPE_REF')
        participant = tier_node.get('PARTICIPANT')
        tier_id = tier_node.get('TIER_ID')
        parent_ref = tier_node.get('PARENT_REF')
        default_locale = tier_node.get('DEFAULT_LOCALE')
        tier = ELANTier(type_ref, participant, tier_id, doc=self, default_locale=default_locale, parent_ref=parent_ref)
        if tier_id in self.__tiers_map:
            raise ValueError("Duplicated tier ID ({})".format(tier_id))
        self.__tiers_map[tier_id] = tier
        if tier.parent_ref is None:
            self.__roots.append(tier)
        return tier

    def _add_timeslot_xml(self, timeslot_node):
        ''' [Internal function] Parse a TimeSlot XML node and link it to current ELANDoc

        General users should not use this function.
        '''
        timeslot = TimeSlot.from_node(timeslot_node)
        self.time_order[timeslot.ID] = timeslot

    def _add_linguistic_type_xml(self, elem):
        ''' [Internal function] Parse a LinguisticType XML node and link it to current ELANDoc

        General users should not use this function.
        '''
        self.__linguistic_types.append(LinguisticType(elem))

    def _add_constraint_xml(self, elem):
        ''' [Internal function] Parse a CONSTRAINT XML node and link it to current ELANDoc

        General users should not use this function.
        '''
        self.__constraints.append(ELANContraint(elem))

    def _add_vocab_xml(self, elem):
        ''' [Internal function] Parse a CONTROLLED_VOCABULARY XML node and link it to current ELANDoc

        General users should not use this function.
        '''
        self.__vocabs.append(ELANVocab.from_xml(elem))

    def to_csv_rows(self) -> CSVTable:
        ''' Convert this ELANDoc into a CSV-friendly structure (i.e. list of list of strings) 
        
        :return: A list of list of strings
        :rtype: CSVTable
        '''
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
    for tier in elan_doc.tiers():
        lingtype = elan_doc.get_linguistic_type(tier._type_ref_id)
        tier._set_type_ref(lingtype)
        lingtype.tiers.append(tier)  # type -> tiers
        if lingtype.vocab:
            lingtype.vocab.tiers.append(tier)  # vocab -> tiers
        if tier.parent_ref is not None:
            tier.parent = elan_doc[tier.parent_ref]
            elan_doc[tier.parent_ref].children.append(tier)


def parse_eaf_stream(eaf_stream):
    ''' Parse an EAF text stream and return an ELAN object

    :param eaf_stream: a text-based stream object
    :type eaf_stream: Text I/O
    :return: an ELANDoc object
    :rtype: texttaglib.elan.ELANDoc
    '''
    elan_doc = ELANDoc()
    current_tier = None
    for event, elem in ET.iterparse(eaf_stream, events=('start', 'end')):
        if event == 'start':
            if elem.tag == 'ANNOTATION_DOCUMENT':
                elan_doc._update_info_xml(elem)
            elif elem.tag == 'TIER':
                current_tier = elan_doc._add_tier_xml(elem)
        elif event == 'end':
            if elem.tag == 'HEADER':
                elan_doc._update_header_xml(elem)
                elem.clear()  # no need to keep header node in memory
            elif elem.tag == 'TIME_SLOT':
                elan_doc._add_timeslot_xml(elem)
                elem.clear()
            elif elem.tag == 'ANNOTATION':
                current_tier._add_annotation_xml(elem)
                elem.clear()
            elif elem.tag == 'LINGUISTIC_TYPE':
                elan_doc._add_linguistic_type_xml(elem)
                elem.clear()
            elif elem.tag == 'CONSTRAINT':
                elan_doc._add_constraint_xml(elem)
                elem.clear()
            elif elem.tag == 'CONTROLLED_VOCABULARY':
                elan_doc._add_vocab_xml(elem)
                elem.clear()
    __resolve(elan_doc)  # link parts together
    return elan_doc


def open_eaf(eaf_path, encoding='utf-8', *args, **kwargs) -> ELANDoc:
    ''' Read and parse an EAF file and return an ELANDoc object 

    :param eaf_path: Path to an EAF file
    :return: An ELANDoc object
    :rtype: texttaglib.elan.ELANDoc
    '''
    
    with chio.open(eaf_path, encoding=encoding, *args, **kwargs) as eaf_stream:
        elan_doc = parse_eaf_stream(eaf_path)
        return elan_doc

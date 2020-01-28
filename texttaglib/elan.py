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
import xml.etree.ElementTree as ET

from chirptext import DataObject
from texttaglib import ttl

from .vtt import sec2ts


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class TimeSlot():
    def __init__(self, ID, value):
        """
        An ELAN timestamp (with ID)
        """
        self.ID = ID
        self.value = value

    @property
    def ts(self):
        return sec2ts(self.sec)

    @property
    def sec(self):
        return self.value / 1000

    @staticmethod
    def from_node(node):
        return TimeSlot(node.get('TIME_SLOT_ID'), int(node.get('TIME_VALUE')))


class ELANAnnotation(DataObject):
    def __init__(self, ID, from_ts, to_ts, value):
        """
        An ELAN annotation
        """
        self.ID = ID
        self.from_ts = from_ts
        self.to_ts = to_ts
        self.value = value

    @property
    def duration(self):
        return self.to_ts.sec - self.from_ts.sec


class ELANTier(DataObject):
    def __init__(self, type_ref, participant, ID, doc=None):
        """
        ELAN Tier Model which contains annotation objects
        """
        self.type_ref = type_ref
        self.participant = participant
        self.ID = ID
        self.doc = doc
        self.annotations = []

    def add_annotation_xml(self, annotation_node):
        ''' Create an annotation from a node '''
        alignable = annotation_node.find('ALIGNABLE_ANNOTATION')  # has to be not None
        if alignable is None:
            raise ValueError("ANNOTATION node must not be empty")
        else:
            ann_id = alignable.get('ANNOTATION_ID')
            from_ts_id = alignable.get('TIME_SLOT_REF1')
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
                value = value_node.text
                anno = ELANAnnotation(ann_id, from_ts, to_ts, value)
                self.annotations.append(anno)
                return anno


class LinguisticType(DataObject):
    def __init__(self, xml_node=None):
        """

        """
        data = {k.lower(): v for k, v in xml_node.attrib.items()} if xml_node is not None else {}
        super().__init__(**data)


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

    def tiers(self):
        return self.tiers_map.values()

    def update_info_xml(self, node):
        self.author = node.get('AUTHOR')
        self.date = node.get('DATE')
        self.fileformat = node.get('FORMAT')
        self.version = node.get('VERSION')
        
    def update_header_xml(self, node):
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
        tier = ELANTier(type_ref, participant, tier_id, self)
        if tier_id in self.tiers_map:
            raise ValueError("Duplicated tier ID ({})".format(tier_id))
        self.tiers_map[tier_id] = tier
        return tier
            
    def add_timeslot_xml(self, timeslot_node):
        timeslot = TimeSlot.from_node(timeslot_node)
        self.time_order[timeslot.ID] = timeslot


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
    return elan_doc

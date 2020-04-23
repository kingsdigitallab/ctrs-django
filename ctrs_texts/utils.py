import json
import os
import re
from collections import Counter

import lxml.etree as ET
from _collections import OrderedDict
from django.conf import settings
from django.utils.text import slugify
from lxml import html


def get_xml_from_unicode(document, ishtml=False, add_root=False):
    # document = a unicode object containing the document
    # ishtml = True will be more lenient about the XML format
    #          and won't complain about named entities (&nbsp;)
    # add_root = True to surround the given document string with
    #         <root> element before parsing. In case there is no
    #        single containing element.

    if document and add_root:
        document = r'<root>%s</root>' % document

    parser = None
    if ishtml:
        from io import StringIO
        parser = ET.HTMLParser()
        # we use StringIO otherwise we'll have encoding issues
        d = StringIO(document)
    else:
        from io import BytesIO
        d = BytesIO(document.encode('utf-8'))
    ret = ET.parse(d, parser)

    return ret


def get_unicode_from_xml(xmltree, encoding='utf-8',
                         text_only=False, remove_root=False):
    # if text_only = True => strip all XML tags
    # EXCLUDE the TAIL
    if text_only:
        return get_xml_element_text(xmltree)
    else:
        # import regex as re

        if hasattr(xmltree, 'getroot'):
            xmltree = xmltree.getroot()
        ret = ET.tostring(xmltree, encoding=encoding).decode('utf-8')
        if xmltree.tail is not None and ret[0] == '<':
            # remove the tail
            ret = re.sub(r'[^>]+$', '', ret)

        if remove_root:
            r = [
                ret.find('<root>'),
                ret.rfind('</root>')
            ]
            if r[0] > 0 and r[1] > r[0]:
                ret = ret[r[0] + len('<root>'):r[1]]

        return ret


def get_xml_element_text(element):
    # returns all the text within element and its descendants
    # WITHOUT the TAIL.
    #
    # element is etree Element object
    #
    # '<r>t0<e1>t1<e2>t2</e2>t3</e1>t4</r>'
    # e = (xml.findall(el))[0]
    # e.text => t1
    # e.tail => t4 (! part of e1)
    # get_xml_element_text(element) => 't1t2t3'

    return ''.join(element.itertext())


def append_xml_element(
    parent_element, tag_name, text=None, prepend=False, **attributes
):
    '''
    Create a new xml element and add it to parent_element.

    If an attribute name is a python reserved word (e.g. class),
    just add _ at the end (e.g. class_).

    Note that _ in attribute name is converted to -.
    E.g. data_something => data-something
    '''

    if attributes:
        attributes = {
            k.rstrip('_').replace('_', '-'): v
            for k, v
            in attributes.items()
        }

    ret = ET.Element(tag_name, attrib=attributes)
    if prepend:
        parent_element.insert(0, ret)
        ret.tail = parent_element.text
        parent_element.text = None
    else:
        parent_element.append(ret)

    if text is not None:
        ret.text = text

    return ret


def get_sentence_from_text(encoded_text, sentence_number):
    ret = ''

    # ac-139 we remove all auxiliary sentences first
    content = re.sub('<p[^>]+data-dpt-type="auxiliary".*?</p>',
                     '', encoded_text.content)

    pattern = ''.join([
        r'(?usi)(<p>\s*<span[^>]+data-rid="s-',
        re.escape(str(sentence_number)),
        r'".*?</p>)\s*(<p>\s*<span data-dpt="sn"|$)'
    ])

    match = re.search(pattern, content)

    if match:
        ret = match.group(1)

    return ret


def get_regions_with_unique_variants(text_ids):
    ret = []

    # build ret: list of all wregions in HM1, in their order of appearance.
    # for each region, ['key'] is a key that will match the annotation key
    # see _get_annotations_from_archetype()
    wpattern = './/span[@data-dpt-group="work"]'

    keys_freq = Counter()

    from ctrs_texts.models import EncodedText

    for encoded_text in EncodedText.objects.filter(
        abstracted_text__short_name__in=['HM1'],
        type__slug='transcription'
    ):
        content = get_xml_from_unicode(
            encoded_text.content, ishtml=True, add_root=True
        )
        for wregion in content.findall(wpattern):
            key = slugify(get_unicode_from_xml(wregion, text_only=True))[:20]
            key = key or '∅'
            keys_freq.update([key])
            freq = keys_freq[key]
            if freq > 1:
                key = '{}:{}'.format(key, freq)
            ret.append({
                'key': key,
                'readings': OrderedDict()
            })

    # for each selected manuscript, get its parent w-regions
    # where all v-regions have been substituted with the content from the MS
    vpattern = './/span[@data-dpt-group="version"]'

    for encoded_text in EncodedText.objects.filter(
        abstracted_text_id__in=text_ids,
        type__slug='transcription',
        abstracted_text__type__slug='manuscript',
    ).order_by('abstracted_text__short_name'):
        member_siglum = encoded_text.abstracted_text.short_name

        # get vregions from member
        vregions = []
        content = get_xml_from_unicode(
            encoded_text.content, ishtml=True, add_root=True
        )
        for vregion in content.findall(vpattern):
            vregions.append(get_unicode_from_xml(vregion, text_only=True))

        # print(vregions)

        # get parent
        parent = EncodedText.objects.filter(
            abstracted_text=encoded_text.abstracted_text.group,
            type__slug='transcription',
        ).first()

        content_parent = get_xml_from_unicode(
            parent.content, ishtml=True, add_root=True
        )
        parent_siglum = parent.abstracted_text.short_name

        # replace vregion in parent with text from member
        for i, vregion in enumerate(content_parent.findall(vpattern)):
            if i < len(vregions):
                vregion.clear(keep_tail=True)
                vregion.text = vregions[i]
            else:
                print('WARNING: v-region #{} of {} not found in {}'.format(
                    i, encoded_text, parent)
                )

        # get the text of all the wregions from parent
        for i, wregion in enumerate(content_parent.findall(wpattern)):
            if i < len(ret):
                wreading = get_unicode_from_xml(wregion, text_only=True)
                wreading = wreading.strip()
                if wreading not in ret[i]['readings']:
                    ret[i]['readings'][wreading] = []
                ret[i]['readings'][wreading].append(
                    [parent_siglum, member_siglum])
            else:
                print('WARNING: w-region #{} of {} not found in {}'.format(
                    i, parent, 'heatmap text (HM1)')
                )

    return ret


def get_annotations_from_archetype():
    '''
    Returns a simplified dictionary of annotations from archetype api.

    ret['principem-regem'] = {
        rects: [
            [
                [994.4017594070153,2871.1062469927056]],
                [1201.1631251142062,2825.8702290932333]
            ]
        ]
    },
    '''
    ret = {}

    annotation_path = os.path.join(
        settings.MEDIA_ROOT, 'arch-annotations.json'
    )
    with open(annotation_path, 'rt') as fh:
        api_response = json.load(fh)

    for a in api_response['results']:
        geo_json = json.loads(a['geo_json'])

        # skip 'ghost' annotations (no properties)
        if not geo_json['properties']:
            continue

        # extract bounds and text from geo_json
        key = ':'.join([
            e[1] for e in
            geo_json['properties']['elementid']
            if e[0].startswith('@')
        ])

        if key not in ret:
            ret[key] = {'rects': []}

        ret[key]['rects'].append([
            geo_json['geometry']['coordinates'][0][0],
            geo_json['geometry']['coordinates'][0][2]
        ])

    return ret


def get_text_chunk(encoded_text, view, region_type):
    if view in ['histogram']:
        '''Returns a list of sentences; for each one, the number of regions'''
        ret = []

        xml = get_xml_from_unicode(
            encoded_text.content, add_root=True, ishtml=True)
        for para in xml.findall('.//p'):
            for sentence_element in para.findall('.//span[@data-dpt="sn"]'):
                number = re.sub(r'^s-(\d+)$', r'\1',
                                sentence_element.attrib.get('data-rid', ''))
                if not number:
                    continue

                regions = para.findall(
                    './/span[@data-dpt-group="' + region_type + '"]')

                res = {
                    'key': number,
                    'value': len(regions),
                }
                ret.append(res)
    else:
        ret = encoded_text.get_content_with_readings()

    return ret


def search_text(encoded_text, query=''):
    if not encoded_text:
        return None

    query = query.lower()

    lowercase = (
        'translate(., '
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZ", '
        '"abcdefghijklmnopqrstuvwxyz")'
    )
    search_pattern = get_text_search_pattern()
    search_xpath = (
        r'.//p[re:match(normalize-space({}), "{}", "i")]'.format(
            lowercase, search_pattern.format(query))
    )

    xml = get_xml_from_unicode(
        encoded_text.content, ishtml=True, add_root=True)

    results = [get_unicode_from_xml(sentence)
               for sentence in xml.xpath(
                   search_xpath,
                   namespaces={'re': 'http://exslt.org/regular-expressions'})
               ]

    return results


def get_text_search_pattern():
    return r'\b{}\w*\b'


def get_plain_text(encoded_text):
    '''Returns the plain text content from an `EncodedText`.'''
    if not encoded_text:
        return None

    xml = html.fromstring(encoded_text.content)
    text = xml.text_content()

    if not text:
        return None

    return text.strip()

import lxml.etree as ET
import re


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

    pattern = ''.join([
        r'(?usi)(<p>\s*<span data-dpt="sn">\s*',
        str(sentence_number),
        r'\s*</span>.*?</p>)(\s*<p>\s*<span data-dpt="sn">|$)'
    ])

    sentences = re.findall(pattern, encoded_text.content)

    if sentences:
        ret = sentences[0][0]

    return ret

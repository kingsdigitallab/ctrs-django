from django.utils.text import slugify
from ctrs_texts.models import AbstractedText, EncodedText
from django.http import JsonResponse
from _collections import OrderedDict
from django.db.models import Q
from django.template.loader import render_to_string
import json
from django.conf import settings
import os
from ctrs_texts.utils import get_xml_from_unicode, get_unicode_from_xml
from collections import Counter


def view_api_texts(request):
    '''
    Returns json with a list of AbstractedTexts.
    For each text, some metadata.

    Output format must follow https://jsonapi.org/

    The list is FLAT.
    Information about hierarchy (MS->V->W)
    is conveyed with the 'group' field.

    http://localhost:8000/api/texts/?group=declaration
    '''

    # returns all texts by default
    abstracted_texts = AbstractedText.objects.all()

    # returns all texts related to a parent/group
    # if ?group=<text.slug>|<text.id> is passed.
    group_slug = request.GET.get('group', None)
    if group_slug:
        abstracted_texts = abstracted_texts.filter(
            Q(slug=group_slug) | Q(group__slug=group_slug) | Q(
                group__group__slug=group_slug
            )
        )

    abstracted_texts = abstracted_texts.exclude(
        short_name__in=['HM1', 'HM2']
    ).select_related(
        'manuscript__repository', 'type'
    ).order_by(
        '-type__slug', 'short_name', 'locus'
    )

    texts = []
    for text in abstracted_texts:
        text_data = [
            ['id', text.id],
            ['type', text.type.slug],
            ['attributes', {
                'slug': text.slug,
                'name': text.name,
                'group': text.group_id,
                'siglum': text.short_name,
            }]
        ]
        text_data = OrderedDict(text_data)
        if text.manuscript:
            text_data['attributes'].update({
                'city': text.manuscript.repository.city or '',
                'repository': text.manuscript.repository.name,
                'shelfmark': text.manuscript.shelfmark,
                'locus': text.locus,
            })

        texts.append(text_data)

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', texts],
    ])

    return JsonResponse(ret)


def view_api_text_chunk(
    request, text_slug, view='transcription', unit='', location=''
):
    '''
    Returns json with the requested data chunk.
    A chunk can be anything: XML, json, html, ...
    http://localhost:8000/api/texts/490/transcription/whole/whole/
    '''
    slugs = text_slug.split(',')
    try:
        filters = {'abstracted_text__id__in': [int(s) for s in slugs]}
    except ValueError:
        filters = {'abstracted_text__slug__in': slugs}

    encoded_texts = EncodedText.objects.filter(
        **filters
    ).filter(type__slug=view)

    data = {}
    if encoded_texts.count() == 1:
        # individual chunk
        encoded_text = encoded_texts[0]
        data = OrderedDict([
            ['id', encoded_text.id],
            ['type', 'text_chunk'],
            ['attributes', OrderedDict([
                ['view', view],
                ['unit', unit],
                ['location', location],
                ['chunk', encoded_text.content_variants()],
            ])],
        ])

    if encoded_texts.count() > 1:
        # TODO: comparative chunk
        pass

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', data],
    ])

    return JsonResponse(ret)

# -------------------------------------------------------------------


def view_api_text_search_sentences(request):
    '''
    '''

    text_ids = request.GET.get('texts', '') or '0'
    text_ids = text_ids.split(',')

    encoded_texts = EncodedText.objects.filter(
        abstracted_text__id__in=text_ids,
        type__slug='transcription'
    ).order_by(
        'abstracted_text__group__short_name',
        'abstracted_text__short_name'
    )

    sentence_number = request.GET.get('sn', '1')

    texts = []
    import re
    for encoded_text in encoded_texts:
        pattern = ''.join([
            r'<p><span data-dpt="sn">\s*',
            sentence_number,
            r'\s*</span>.*?</p>'
        ])
        sentence = ''
        sentences = re.findall(pattern, encoded_text.content)
        if sentences:
            sentence = sentences[0]

        html = render_to_string('ctrs_texts/search_sentence.html', {
            'text': encoded_text.abstracted_text,
            'sentence': sentence,
        })

        text_data = {
            'html': html,
        }
        texts.append(text_data)

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', texts],
    ])

    return JsonResponse(ret)

# -------------------------------------------------------------------


def view_api_text_search_regions(request):
    '''
    '''

    text_ids = request.GET.get('texts', '') or '520'
    text_ids = text_ids.split(',')

    annotation_path = os.path.join(
        settings.MEDIA_ROOT, 'arch-annotations.json'
    )
    with open(annotation_path, 'rt') as fh:
        annotations_res = json.load(fh)

    annotations = _get_annotations_from_archetype(annotations_res)

    hits = [{
        'type': 'heatmap',
        'id': 0,
        'html': render_to_string('ctrs_texts/search_region.html', {}),
        'regions': _get_regions_with_unique_variants(text_ids),
        'annotations': annotations,
    }]

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', hits],
    ])

    return JsonResponse(ret)


def _get_regions_with_unique_variants(text_ids):
    ret = []

    wpattern = './/span[@data-dpt-group="work"]'

    rids = Counter()
    for encoded_text in EncodedText.objects.filter(
        abstracted_text__short_name__in=['HM1'],
        type__slug='transcription'
    ):
        content = get_xml_from_unicode(
            encoded_text.content, ishtml=True, add_root=True
        )
        for wregion in content.findall(wpattern):
            rid = slugify(get_unicode_from_xml(wregion, text_only=True))[:20]
            rid = rid or '∅'
            rids.update([rid])
            c = rids[rid] - 1
            if c:
                rid = '{}:{}'.format(rid, c)
            print(rid)
            ret.append({
                'id': rid
            })

    vpattern = './/span[@data-dpt-group="version"]'

    for encoded_text in EncodedText.objects.filter(
        abstracted_text_id__in=text_ids,
        type__slug='transcription',
        abstracted_text__type__slug='manuscript',
    ):
        parent = EncodedText.objects.filter(
            abstracted_text=encoded_text.abstracted_text.group,
            type__slug='transcription',
        ).first()

        content_parent = get_xml_from_unicode(
            parent.content, ishtml=True, add_root=True
        )

        vregions = []
        content = get_xml_from_unicode(
            encoded_text.content, ishtml=True, add_root=True
        )
        for vregion in content.findall(vpattern):
            vregions.append(get_unicode_from_xml(wregion, text_only=True))

        for i, vregion in enumerate(content_parent.findall(vpattern)):
            if i < len(vregions):
                vregion.text = vregions[i]
            else:
                print('WARNING: region #{} of {} not found in {}'.format(
                    i, encoded_text, parent)
                )

    return ret


def _get_annotations_from_archetype(api_response):
    '''
    Returns a list of simplified annotation dictionaries from archetype api.
    '''
    ret = []
    for a in api_response['results']:
        geo_json = json.loads(a['geo_json'])

        # skip 'ghost' annotations (no properties)
        if geo_json['properties']:
            # extract bounds and text from geo_json
            ret.append(a)
            a['bounds'] = [
                geo_json['geometry']['coordinates'][0][0],
                geo_json['geometry']['coordinates'][0][2]
            ]
            a['text'] = ':'.join([
                e[1] for e in
                geo_json['properties']['elementid']
                if e[0].startswith('@')
            ])
            del(a['geo_json'])

    return ret

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
from .. import utils


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
    sentence_number = request.GET.get('sn', '1')
    encoding_type = request.GET.get('et', 'transcription')

    encoded_texts = EncodedText.objects.filter(
        abstracted_text__id__in=text_ids,
        type__slug=encoding_type
    ).order_by(
        'abstracted_text__group__short_name',
        'abstracted_text__short_name'
    )

    texts = []
    for encoded_text in encoded_texts:
        sentence = utils.get_sentence_from_text(
            encoded_text, sentence_number
        )

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

    annotations = _get_annotations_from_archetype()

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

    # build ret: list of all wregions in HM1, in their order of appearance.
    # for each region, ['key'] is a key that will match the annotation key
    # see _get_annotations_from_archetype()
    wpattern = './/span[@data-dpt-group="work"]'

    keys_freq = Counter()
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


def _get_annotations_from_archetype():
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

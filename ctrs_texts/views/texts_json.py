from ctrs_texts.models import AbstractedText, EncodedText
from django.http import JsonResponse
from _collections import OrderedDict
from django.db.models import Q
from django.template.loader import render_to_string
import json
from django.conf import settings
import os


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

    text_ids = request.GET.get('texts', '') or '520'
    text_ids = text_ids.split(',')

    encoded_texts = EncodedText.objects.filter(
        abstracted_text__id__in=text_ids,
        type__slug='transcription'
    )

    texts = []
    for text in encoded_texts:
        text_data = {
            # 'chunk': re.findall(
            # r'<p><span data-dpt="sn">(.?*)</span>.*?</p>', '', text.content),
            'chunk': text.id,
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

    hits = [{
        'type': 'heatmap',
        'id': 0,
        'html': render_to_string('ctrs_texts/search_region.html', {}),
        'annotations': json.load(annotations_res)['results']
    }]

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', hits],
    ])

    return JsonResponse(ret)

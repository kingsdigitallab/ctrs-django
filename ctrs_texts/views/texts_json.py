import re

from _collections import OrderedDict
from ctrs_texts.models import AbstractedText, EncodedText
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string

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

    encoded_type = view
    if view in ['histogram']:
        encoded_type = 'transcription'

    try:
        filters = {'abstracted_text__id__in': [int(s) for s in slugs]}
    except ValueError:
        filters = {'abstracted_text__slug__in': slugs}

    encoded_texts = EncodedText.objects.filter(
        **filters
    ).filter(type__slug=encoded_type)

    data = {}
    if encoded_texts.count() == 1:
        # individual chunk
        encoded_text = encoded_texts[0]

        region_type = encoded_text.abstracted_text.type.slug
        if region_type not in ['work', 'version']:
            region_type = 'version'

        data = OrderedDict([
            ['id', encoded_text.id],
            ['type', 'text_chunk'],
            ['attributes', OrderedDict([
                ['view', view],
                ['unit', unit],
                ['location', location],
                ['value_max', 17],
                ['region_type', region_type],
                ['description', 'number of unsettled regions per sentence'],
                ['chunk', utils.get_text_chunk(
                    encoded_text, view, region_type)],
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

    # TODO: GN remove hard-coded id
    text_ids = request.GET.get('texts', '') or '520'
    text_ids = text_ids.split(',')

    annotations = utils.get_annotations_from_archetype()

    hits = [{
        'type': 'heatmap',
        'id': 0,
        'html': render_to_string('ctrs_texts/search_region.html', {}),
        'regions': utils.get_regions_with_unique_variants(text_ids),
        'annotations': annotations,
    }]

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['data', hits],
    ])

    return JsonResponse(ret)


def view_api_text_search_text(request):
    q = request.GET.get('q', '')
    if q:
        q = q.strip()

    text_ids = request.GET.get('texts', None)
    encoding_type = request.GET.get('et', 'transcription')

    encoded_texts = EncodedText.objects.filter(type__slug=encoding_type)

    if text_ids:
        text_ids = text_ids.split(',')
        encoded_texts = encoded_texts.filter(abstracted_text__id__in=text_ids)

    # match only words that begin with the search query
    # needs to use PSQL regex syntax, not Python's
    # https://www.postgresql.org/docs/9.4/functions-matching.html#POSIX-CONSTRAINT-ESCAPES-TABLE
    encoded_texts = encoded_texts.filter(
        plain__iregex=r'\m{}'.format(q)).order_by(
        'abstracted_text__group__short_name',
        'abstracted_text__short_name'
    )

    search_pattern = utils.get_text_search_pattern()
    escaped = '|'.join([search_pattern.format(w) for w in q.split()])
    # pattern to highlight the search results
    # https://regexr.com/532qa
    highlight_pattern = re.compile(
        '({})(?=(?:[^>]|<[^>]*>)*$)'.format(escaped), re.I)

    sentences = []
    for encoded_text in encoded_texts:
        for sentence in utils.search_text(encoded_text, q):
            html = render_to_string('ctrs_texts/search_sentence.html', {
                'text': encoded_text.abstracted_text,
                'sentence': sentence,
            })

            # highlight the search results
            if q:
                html = highlight_pattern.sub(
                    r'<span class="highlight">\1</span>', html)

            sentence_data = {
                'html': html,
            }

            sentences.append(sentence_data)

    ret = OrderedDict([
        ['jsonapi', '1.0'],
        ['q', q],
        ['data', sentences],
    ])

    return JsonResponse(ret)

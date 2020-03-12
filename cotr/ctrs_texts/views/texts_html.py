from ctrs_texts.models import AbstractedText, EncodedText, EncodedTextType
from django.shortcuts import render


def view_text_viewer(request):
    '''
    New text viewer: multi-text, multi-views
    '''
    context = {
        'awesome_pseudo': True,
    }
    ret = render(request, 'ctrs_texts/text_viewer.html', context)
    return ret


def view_texts(request):
    '''
    The list of all Works, Versions and Texts
    with links to the Text Viewer.
    '''
    context = {
        'works': AbstractedText.objects.filter(
            # encoded_texts__status__slug='to-be-reviewed'
            type__slug='work',
        ),
        'view_default': 'transcription',
    }

    return render(request, 'ctrs_texts/texts.html', context)


def view_text_search(request):
    '''
    '''
    context = {
    }

    return render(request, 'ctrs_texts/text_search.html', context)

# -----------------------------------------------------------------------


def view_text_viewer_legacy(request, text_slug, view='transcription'):
    '''
    Legacy single text viewer.
    To be removed when we have a working version of the text viewer.
    '''
    text_views = EncodedTextType.get_all()
    for k, v in text_views.items():
        if k != view:
            view_alternative = v
            break

    context = {
        'encoded_text': EncodedText.objects.filter(
            abstracted_text__slug=text_slug,
            type=text_views.get(view)
        ).first(),
        'view_alternative': view_alternative,
    }
    ret = render(request, 'ctrs_texts/text_viewer_legacy.html', context)
    return ret

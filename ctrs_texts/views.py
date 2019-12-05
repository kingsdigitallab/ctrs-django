# from django.shortcuts import render
from django.shortcuts import render
from ctrs_texts.models import AbstractedText, EncodedText, EncodedTextType

# Create your views here.


def view_text_viewer(request, text_slug, view_slug='transcription'):
    text_views = EncodedTextType.get_all()
    for k, v in text_views.items():
        if k != view_slug:
            view_alternative = v
            break

    context = {
        'encoded_text': EncodedText.objects.filter(
            abstracted_text__slug=text_slug,
            type=text_views.get(view_slug)
        ).first(),
        'view_alternative': view_alternative,
    }
    ret = render(request, 'ctrs_texts/text_viewer.html', context)
    return ret


def view_texts(request):
    context = {
        'works': AbstractedText.objects.filter(
            # encoded_texts__status__slug='to-be-reviewed'
            type__slug='work',
        ),
        'view_default': 'transcription',
    }
    return render(request, 'ctrs_texts/texts.html', context)

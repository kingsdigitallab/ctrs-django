# from django.shortcuts import render
from django.shortcuts import render
from ctrs_texts.models import AbstractedText, EncodedText

# Create your views here.


def view_text_viewer(request, slug):
    context = {
        'encoded_text': EncodedText.objects.filter(
            abstracted_text__slug=slug,
            type__slug='transcription'
        ).first()
    }
    return render(request, 'ctrs_texts/text_viewer.html', context)


def view_texts(request):
    context = {
        'works': AbstractedText.objects.filter(
            # encoded_texts__status__slug='to-be-reviewed'
            type__slug='work',
        )
    }
    return render(request, 'ctrs_texts/texts.html', context)

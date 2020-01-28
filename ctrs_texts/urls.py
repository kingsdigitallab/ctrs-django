# from django.conf import settings
from django.urls import path
from django.contrib import admin
from .views.texts_html import (
    view_texts, view_text_search,
    view_text_viewer, view_text_viewer_legacy,
)
from .views.texts_json import (
    view_api_texts, view_api_text_chunk, view_api_text_search_sentences
)

admin.autodiscover()

urlpatterns = [
    # List of all texts
    path('texts/', view_texts, name="texts"),

    # New Text Viewer (multi-texts and multi-views)
    path('texts/viewer/',
         view_text_viewer, name='text_viewer'),

    path('texts/search/',
         view_text_search, name='text_search'),

    # Standard Text API
    path(
        'api/texts/',
        view_api_texts, name='view_api_texts'
    ),
    path(
        'api/texts/<str:text_slug>/<slug:view>/<slug:unit>/<slug:location>/',
        view_api_text_chunk, name='view_api_text_chunk'
    ),

    # COTR Search API
    path(
        'api/texts/search/sentences/',
        view_api_text_search_sentences, name='view_api_text_search_sentence'
    ),

    # Legacy Text Viewer (only one text at a time)
    path('texts/<slug:text_slug>/<slug:view>/',
         view_text_viewer_legacy, name='text_viewer_legacy'),
]

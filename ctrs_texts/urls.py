# from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from .views.texts_html import (
    view_text_search,
    view_text_viewer,
    view_text_viewer_legacy,
)
from .views.texts_json import (
    view_api_text_chunk,
    view_api_text_search_regions,
    view_api_text_search_sentences,
    view_api_text_search_text,
    view_api_texts,
)

admin.autodiscover()

urlpatterns = [
    # List of all texts -> replaced by a wagtail page with text_list block
    # TODO: remove when confirmed we no longer need this
    # path('texts/', view_texts, name="texts"),

    # New Text Viewer (multi-texts and multi-views)
    path('viewer/',
         view_text_viewer, name='text_viewer'),

    # New Text Viewer (multi-texts and multi-views)
    # e.g. /test/viewer?blocks=506:translation;
    path(
        'texts/viewer/',
        RedirectView.as_view(
            pattern_name='text_viewer',
            permanent=False,
            query_string=True
        )
    ),

    path('search/',
         view_text_search, name='text_search'),

    # New Text Viewer (multi-texts and multi-views)
    # e.g. /test/viewer?blocks=506:translation;
    path(
        'texts/search/',
        RedirectView.as_view(
            pattern_name='text_search',
            permanent=False,
            query_string=True
        )
    ),

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
        'api/texts/search/text/',
        view_api_text_search_text, name='view_api_text_search_text'
    ),
    path(
        'api/texts/search/sentences/',
        view_api_text_search_sentences, name='view_api_text_search_sentence'
    ),
    path(
        'api/texts/search/regions/',
        view_api_text_search_regions, name='view_api_text_search_regions'
    ),

    # Legacy Text Viewer (only one text at a time)
    # TODO: remove when sure we no longer need it
    path('legacy/texts/<slug:text_slug>/<slug:view>/',
         view_text_viewer_legacy, name='text_viewer_legacy'),
]

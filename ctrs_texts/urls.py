# from django.conf import settings
from django.urls import path, re_path
from django.contrib import admin
from .views import view_texts, view_text_viewer

admin.autodiscover()

urlpatterns = [
    path(r'texts/', view_texts, name="texts"),
    re_path(r'texts/(?P<text_slug>[^/]+)/(?P<view_slug>[^/]+)/',
            view_text_viewer, name='text_view'),
]

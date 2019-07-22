# from django.conf import settings
from django.urls import path, re_path
from django.contrib import admin
from .views import view_texts, view_text_viewer

admin.autodiscover()

urlpatterns = [
    path(r'texts/', view_texts, name="texts"),
    re_path(r'texts/(?P<slug>[^/]+)/content/',
            view_text_viewer, name='text_view'),
]

from django.conf import settings
from django.urls import include, path, re_path
from django.contrib import admin
from django.views.generic import TemplateView

from kdl_ldap.signal_handlers import \
    register_signal_handlers as kdl_ldap_register_signal_hadlers

kdl_ldap_register_signal_hadlers()


admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('digger/', include('activecollab_digger.urls')),

    path('wagtail/', include('wagtail.admin.urls')),
    path('documents/', include('wagtail.documents.urls')),
    # GN 'static' mockup, renamed to .bk so it doesn't clash with new location
    # of the viewer.
    # TODO: remove when no longer
    path('viewer.bk/', TemplateView.as_view(
        template_name='viewer/mocks/viewer.html')),
    path('', include('ctrs_texts.urls')),
    path('', include('wagtail.core.urls')),
]

# -----------------------------------------------------------------------------
# Django Debug Toolbar URLS
# -----------------------------------------------------------------------------
try:
    if settings.DEBUG:
        import debug_toolbar
        urlpatterns = [
            re_path(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
except ImportError:
    pass

# -----------------------------------------------------------------------------
# Static file DEBUGGING
# -----------------------------------------------------------------------------
if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    import os.path

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL + 'images/',
                          document_root=os.path.join(settings.MEDIA_ROOT,
                                                     'images'))

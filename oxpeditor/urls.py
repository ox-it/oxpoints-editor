import os
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^', include('oxpeditor.core.urls', namespace='core')),
    (r'^webauth/', include('oxpeditor.webauth.urls', namespace='webauth')),

    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
    )


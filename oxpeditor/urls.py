import os
from django.conf.urls import *
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^', include('oxpeditor.core.urls', namespace='core')),
    (r'^', include('oxpeditor.linkcheck.urls', namespace='linkcheck')),
    (r'^webauth/', include('oxpeditor.webauth.urls', namespace='webauth')),

    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()

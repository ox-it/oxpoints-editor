import os
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

admin.autodiscover()

urlpatterns = [
    # Example:
    url(r'^', include('oxpeditor.core.urls')),
    url(r'^', include('oxpeditor.linkcheck.urls')),
    url(r'^webauth/', include('oxpeditor.webauth.urls')),

    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()

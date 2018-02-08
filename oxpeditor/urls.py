import os
from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

admin.autodiscover()

urlpatterns = [
    # Example:
    url(r'^', include('oxpeditor.core.urls')),
    url(r'^', include('oxpeditor.linkcheck.urls')),
    url(r'^webauth/', include('oxpeditor.webauth.urls')),

    path('admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


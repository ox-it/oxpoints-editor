from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^links/$', views.LinkView.as_view(), name='links'),
)
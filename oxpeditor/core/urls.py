from django.conf.urls import *

from . import views

app_name = 'core'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^diff/$', views.DiffView.as_view(), name='diff'),
    url(r'^list/$', views.ListView.as_view(), name='list'),
    url(r'^tree/$', views.TreeView.as_view(root_elem='org'), name='tree'),
    url(r'^commit/$', views.CommitView.as_view(), name='commit'),
    url(r'^request/$', views.RequestView.as_view(), name='request'),
    url(r'^linking-you/$', views.LinkingYouView.as_view(), name='linking-you'),
    url(r'^(?P<oxpid>\d{8})/$', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<oxpid>\d{8}(,\d{8})*)/tree/$', views.TreeView.as_view(), name='detail-tree'),
    url(r'^(?P<oxpid>\d{8})/revert/$', views.RevertView.as_view(), name='detail-revert'),

    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<oxpid>\d{8})/create/$', views.CreateView.as_view(), name='detail-create'),

    url(r'^help/$', views.HelpView.as_view(), name='help'),

    url(r'^autosuggest:(?P<active_type>\w+):(?P<relation_name>\w+)/$', views.AutoSuggestView.as_view(), name='autosuggest'),
]

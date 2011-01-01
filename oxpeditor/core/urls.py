from django.conf.urls.defaults import *

from .views import IndexView, DiffView, ListView, TreeView, DetailView, CommitView, RequestView, AutoSuggestView

urlpatterns = patterns('',
    (r'^$', IndexView(), {}, 'index'),
    (r'^diff/$', DiffView(), {}, 'diff'),
    (r'^list/$', ListView(), {}, 'list'),
    (r'^tree/$', TreeView(root_elem='org'), {}, 'tree'),
    (r'^commit/$', CommitView(), {}, 'commit'),
    (r'^request/$', RequestView(), {}, 'request'),
    (r'^(?P<oxpid>\d{8})/$', DetailView(), {}, 'detail'),
    (r'^(?P<oxpid>\d{8})/tree/$', TreeView(), {}, 'detail-tree'),

    (r'^autosuggest:(?P<name>\w+)/$', AutoSuggestView(), {}, 'autosuggest'),

)

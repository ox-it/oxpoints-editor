from django.conf.urls.defaults import *

from .views import IndexView, SearchView, DiffView, ListView, TreeView, DetailView, CommitView, RequestView

urlpatterns = patterns('',
    (r'^$', IndexView(), {}, 'index'),
    (r'^search/$', SearchView(), {}, 'search'),
    (r'^diff/$', DiffView(), {}, 'diff'),
    (r'^list/$', ListView(), {}, 'list'),
    (r'^tree/$', TreeView(root_elem='org'), {}, 'tree'),
    (r'^commit/$', CommitView(), {}, 'commit'),
    (r'^request/$', RequestView(), {}, 'request'),
    (r'^(?P<oxpid>\d{8})/$', DetailView(), {}, 'detail'),
    (r'^(?P<oxpid>\d{8})/tree/$', TreeView(), {}, 'detail-tree'),

)

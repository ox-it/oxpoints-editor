from django.conf.urls import *

from . import views

urlpatterns = patterns('',
    (r'^$', views.IndexView.as_view(), {}, 'index'),
    (r'^diff/$', views.DiffView.as_view(), {}, 'diff'),
    (r'^list/$', views.ListView.as_view(), {}, 'list'),
    (r'^tree/$', views.TreeView.as_view(root_elem='org'), {}, 'tree'),
    (r'^commit/$', views.CommitView.as_view(), {}, 'commit'),
    (r'^request/$', views.RequestView.as_view(), {}, 'request'),
    (r'^(?P<oxpid>\d{8})/$', views.DetailView.as_view(), {}, 'detail'),
    (r'^(?P<oxpid>\d{8}(,\d{8})*)/tree/$', views.TreeView.as_view(), {}, 'detail-tree'),
    (r'^(?P<oxpid>\d{8})/revert/$', views.RevertView.as_view(), {}, 'detail-revert'),
    
    (r'^create/$', views.CreateView.as_view(), {}, 'create'),
    (r'^(?P<oxpid>\d{8})/create/$', views.CreateView.as_view(), {}, 'detail-create'),
    
    (r'^help/$', views.HelpView.as_view(), {}, 'help'),

    (r'^autosuggest:(?P<active_type>\w+):(?P<relation_name>\w+)/$', views.AutoSuggestView.as_view(), {}, 'autosuggest'),

)

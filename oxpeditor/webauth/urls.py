from django.conf.urls import *

from . import views

urlpatterns = patterns('',
    (r'^$', views.IndexView.as_view(), {}, 'index'),
    (r'^login/$', views.LoginView.as_view(), {}, 'login'),
    (r'^logout/$', views.LogoutView.as_view(), {}, 'logout'),

)

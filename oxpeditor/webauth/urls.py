from django.conf.urls import *

from .views import IndexView, LoginView, LogoutView

urlpatterns = patterns('',
    (r'^$', IndexView(), {}, 'index'),
    (r'^login/$', LoginView(), {}, 'login'),
    (r'^logout/$', LogoutView(), {}, 'logout'),

)

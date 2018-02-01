from django.conf.urls import url

from . import views

app_name = 'linkcheck'

urlpatterns = [
    url(r'^links/$', views.LinkView.as_view(), name='links'),
]
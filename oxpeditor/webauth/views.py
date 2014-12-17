from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django_conneg.views import HTMLView

from oxpeditor.utils.views import BaseView
from oxpeditor.utils.http import HttpResponseSeeOther

class IndexView(HTMLView):
    pass

class LoginView(HTMLView):
    def get(self, request):
        username = request.META.get('REMOTE_USER')
        if not username:
            raise ImproperlyConfigured('This view is supposed to set a REMOTE_USER environment variable')

        user = authenticate(username=username)
        login(request, user)

        return HttpResponseSeeOther(request.GET.get('next', reverse('core:index')))

class LogoutView(HTMLView):
    template_name = 'logout'

    def get(self, request):
        logout(request)
        return self.render()


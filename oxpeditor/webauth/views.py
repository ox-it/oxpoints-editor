from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout

from oxpeditor.utils.views import BaseView
from oxpeditor.utils.http import HttpResponseSeeOther

class IndexView(BaseView):
    pass

class LoginView(BaseView):
    def handle_GET(self, request, context):
        username = request.META.get('REMOTE_USER')
        if not username and settings.DEBUG:
            username = 'kebl2765'
        elif not username:
            raise ImproperlyConfigured('This view is supposed to set a REMOTE_USER environment variable')

        user = authenticate(username=username)
        login(request, user)

        return HttpResponseSeeOther(request.GET.get('next', reverse('core:index')))

class LogoutView(BaseView):
    def handle_GET(self, request, context):
        logout(request)

        return self.render(request, context, 'logout')


from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import authenticate, login

from oxpeditor.utils.views import BaseView

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
        print user
        login(request, user)

        return HttpResponseSeeOther(request.GET.get('next', reverse('core:index')))

class LogoutView(BaseView):
    pass


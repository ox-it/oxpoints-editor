from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View, TemplateView


class LoginView(View):
    def get(self, request):
        username = request.META.get('REMOTE_USER', 'kebl2765')
        if not username:
            raise ImproperlyConfigured('This view is supposed to set a REMOTE_USER environment variable')

        user = authenticate(username=username, request_meta=request.META)
        login(request, user)

        return redirect(request.GET.get('next', reverse('core:index')))


class LogoutView(TemplateView):
    template_name = 'logout.html'

    def get(self, request):
        logout(request)
        return super().get(request)


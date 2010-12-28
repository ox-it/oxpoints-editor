from django.contrib.auth.models import User

from .models import Object

def core(request):
    recent = []
    for oxpid in request.session.get('recent', ()):
        try:
            recent.append(Object.objects.get(oxpid=oxpid))
        except Object.DoesNotExist:
            pass
    return {
        'recent': recent,
        'pending_commit': Object.objects.filter(user=request.user).count() if isinstance(request.user, User) else 0,
    }

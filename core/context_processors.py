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
    }

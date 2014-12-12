from django.db.models.signals import post_syncdb
from django.contrib.auth import get_user_model

def create_conflict_user(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(username='conflict').exists():
        User.objects.create_user('conflict')

post_syncdb.connect(create_conflict_user)


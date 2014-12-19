from django.db.models.signals import post_syncdb
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def create_conflict_user(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(username='conflict').exists():
        User.objects.create_user('conflict')

# Get the contenttypes post_syncdb hook called before ours.
import django.contrib.contenttypes.management

def allow_itss_editing(sender, **kwargs):
    itss_group, _ = Group.objects.get_or_create(name='itss')

    content_type = ContentType.objects.get(app_label='core', model='object')
    permission = Permission.objects.get(content_type=content_type, codename='change_object')
    itss_group.permissions.add(permission)

post_syncdb.connect(create_conflict_user)
post_syncdb.connect(allow_itss_editing)


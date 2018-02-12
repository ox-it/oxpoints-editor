import ldap3
import re

from django.conf import settings
from django.contrib.auth.models import User, Group


class ShibbolethBackend(object):
    attribute_map = [
        ('givenName', 'first_name'),
        ('sn', 'last_name'),
        ('mail', 'email'),
    ]
    def authenticate(self, username, request_meta):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username)

        for shib_attribute, user_attribute in self.attribute_map:
            if shib_attribute in request_meta:
                setattr(user, user_attribute, request_meta[shib_attribute])
            else:
                setattr(user, user_attribute, user._meta.fields_map[user_attribute].default)

        user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


import ldap3
import re

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models import Q


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

        groups = {
            'status:{}'.format(request_meta['oakStatus']),
        }

        for orgunit_dn in request_meta.get('orgunit-dn', '').split(';'):
            match = re.match('oakUnitCode=(.*),ou=units,dc=oak,dc=ox,dc=ac,dc=uk', orgunit_dn)
            if match:
                groups.add('affilition:{}'.format(match.group(1)))

        for oak_itss_for in request_meta.get('oakITSSFor', '').split(';'):
            match = re.match('oakGN=ITSS,oakUnitCode=(.*),ou=units,dc=oak,dc=ox,dc=ac,dc=uk', oak_itss_for)
            if match:
                groups.add('itss')
                groups.add('itss:{}'.format(match.group(1)))

        user.groups.remove(*user.groups.exclude(name__in=groups).filter(Q(name='itss') | Q(name__startswith='itss:') |
                                                                       Q(name__startswith='affiliation:') |
                                                                       Q(name__startswith='status:')))
        user.groups.add(*[Group.objects.get_or_create(g)[0] for g in groups])

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


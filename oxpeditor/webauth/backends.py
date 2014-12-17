import ldap, ldap.sasl
import os
import re

from django.conf import settings
from django.contrib.auth.models import User, Group

class WebauthBackend(object):
    def authenticate(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username)
        
        auth = ldap.sasl.gssapi('')
        oakldap = ldap.initialize('ldap://ldap.oak.ox.ac.uk:389')
        oakldap.start_tls_s()
        oakldap.sasl_interactive_bind_s('', auth)

        results = oakldap.search_s('ou=people,dc=oak,dc=ox,dc=ac,dc=uk',
                                   ldap.SCOPE_SUBTREE,
                                   '(oakPrincipal=krbPrincipalName=%s@OX.AC.UK,cn=OX.AC.UK,cn=KerberosRealms,dc=oak,dc=ox,dc=ac,dc=uk)' % username)

        if not results:
            return None
        person = results[0][1]

        user.first_name = person['givenName'][0]
        user.last_name = person['sn'][0]
        user.email = person['mail'][0]
        
        groups = set('status:%s' % s for s in person['oakStatus'])
        for g in person.get('oakITSSFor', ()):
            match = re.match(r'oakGN=ITSS,oakUnitCode=(\w+),ou=units,dc=oak,dc=ox,dc=ac,dc=uk', g)
            if match:
                groups.add('itss:%s' % match.group(1))
            elif g == 'oakGN=ITSS,ou=oucscentral,dc=oak,dc=ox,dc=ac,dc=uk':
                groups.add('itss')
        for u in person.get('eduPersonOrgUnitDN', ()):
            match = re.match(r'oakUnitCode=(\w+),ou=units,dc=oak,dc=ox,dc=ac,dc=uk', u)
            if match:
                groups.add('affiliation:%s' % match.group(1))

        user.groups = set(Group.objects.get_or_create(name=name)[0] for name in groups)
        user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


import os
from imp import find_module

from dns import resolver

from django.core.management.base import BaseCommand
from django.template import loader, Context
from django.conf import settings

import oxpeditor

class Command(BaseCommand):

    def handle(self, *args, **objects):
        project_root = os.path.normpath(os.path.dirname(oxpeditor.__file__))
        server_ip = resolver.query(settings.SERVER_NAME)[0].address
        server_name = settings.SERVER_NAME

        template = loader.get_template('apache.conf')
        context = Context({
            'project_root': project_root,
            'django_root': find_module('django')[1],
            'root': os.path.normpath(os.path.join(project_root, '..')),
            'server_ip': server_ip,
            'server_name': server_name,
        })

        return template.render(context)


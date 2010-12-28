from os import stat
from stat import ST_MTIME
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from oxpeditor.core.models import File

import os
from lxml import etree

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

class Command(BaseCommand):

    def handle(self, *args, **objects):
        filenames = os.listdir(settings.REPO_PATH)

        for filename in filenames:
            fn = os.path.join(settings.REPO_PATH, filename)
            if not filename.endswith('.xml'):
                continue
            mtime = datetime.fromtimestamp(stat(fn)[ST_MTIME])

            try:
                file_obj = File.objects.get(filename=filename)
            except File.DoesNotExist:
                file_obj = File(filename=filename)

            print filename, mtime
            if file_obj.last_modified and file_obj.last_modified >= mtime:
                continue

            xml = etree.parse(open(fn))

            if file_obj.last_modified and file_obj.last_modified < mtime and file_obj.user:
                file_obj.initial_xml = etree.tostring(xml)
                file_obj.user = User.objects.get(username='conflict')
                file_obj.last_modified = mtime
                file_obj.save()


            file_obj.initial_xml = file_obj.xml = etree.tostring(xml)
            file_obj.last_modified = mtime
            file_obj.save()
                

        for file_obj in File.objects.all():
            if file_obj.filename not in filenames:
                file_obj.delete()


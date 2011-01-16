from os import stat
from stat import ST_MTIME
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from oxpeditor.core.models import File
from oxpeditor.core import subversion

import os
from lxml import etree

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

class Command(BaseCommand):

    def handle(self, *args, **objects):
        subversion.perform_update(force=True)

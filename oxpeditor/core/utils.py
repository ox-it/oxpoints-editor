from __future__ import with_statement

import fcntl
import os
import random
from contextlib import contextmanager
from datetime import date, timedelta
from contextlib import closing

from lxml import etree

from django.conf import settings

def _ignore(a, b):
    b.attrib['ignore'] = 'true'
def _remove(a, b):
    a.remove(b)

def date_filter(doc, dt=None, ignore=False):
    dt = dt or date.today().strftime('%Y-%m-%d')
    dt = dt or date.today().strftime('%Y-%m-%d')

    f = _ignore if ignore else _remove

    if hasattr(doc, 'getroot'):
        doc = doc.getroot()

    for e in list(doc):
        if e.attrib.get('from', dt) <= dt < e.attrib.get('to', '9999-12-31'):
            date_filter(e, dt, ignore)
        else:
            f(doc, e) 
            if ignore:
                date_filter(e, dt, ignore)

    return doc

@contextmanager
def svn_lock():
    with open(os.path.join(settings.REPO_PATH, '.oxpeditor.lock'), 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
            
def find_new_oxpids():
    from .models import File
    oxpids = set()
    for file_obj in File.objects.all():
        xml = etree.fromstring(file_obj.xml)
        oxpids |= set(e.attrib['oxpID'] for e in xml.xpath('ancestor-or-self::*[@oxpID]'))
    
    while True:
        oxpid = '5' + ''.join(random.choice('01234589') for i in range(7))
        if oxpid not in oxpids:
            oxpids.add(oxpid)
            yield oxpid

def find_new_oxpid():
    with closing(find_new_oxpids()) as g:
        return g.next()


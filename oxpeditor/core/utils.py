from __future__ import with_statement

import fcntl
import os
from contextlib import contextmanager
from datetime import date, timedelta

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

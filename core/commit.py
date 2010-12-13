import os
import stat
import subprocess
import tempfile
from datetime import datetime

from lxml import etree

from django.conf import settings

from .models import File

def save_to_disk(file_obj, filename):
    xml = etree.fromstring(file_obj.xml)
    open(filename, 'w').write(etree.tostring(xml, xml_declaration=True, encoding="UTF-8"))

def perform_commit(user, message):
    os.chdir(settings.REPO_PATH)

    to_commit = set([])
    for file_obj in File.objects.filter(user=user):
        filename = os.path.join(settings.REPO_PATH, file_obj.filename)
        print file_obj.id, filename, file_obj.last_modified, datetime.fromtimestamp(os.stat(filename)[stat.ST_MTIME])
        if not os.path.exists(filename):
            save_to_disk(file_obj, filename)
            subprocess.call(['svn', 'add', filename])
        elif file_obj.last_modified > datetime.fromtimestamp(os.stat(filename)[stat.ST_MTIME]):
            save_to_disk(file_obj, filename)
        else:
            continue
        to_commit.add(file_obj)

    if not to_commit:
        return

    message = "%s\n\n  -- %s %s (%s)\n" % (message, user.first_name, user.last_name, user.username)

    message_file = tempfile.NamedTemporaryFile(delete=False)
    message_file.write(message)
    message_file.close()

    while True:
        ret = subprocess.call(['svn', 'commit', '--username', 'kebl2765',
                                                '--password', 'ayeminusblood',
                                                '-F', message_file.name])
        if ret == 0:
            break
        to_commit -= perform_update()

    os.unlink(message_file.name)

    for file_obj in to_commit:
        filename = os.path.join(settings.REPO_PATH, file_obj.filename)
        file_obj.initial_xml = file_obj.xml
        file_obj.user = None
        file_obj.last_modified = datetime.fromtimestamp(os.stat(filename)[stat.ST_MTIME])
        file_obj.save()
    
def perform_update():
    raise NotImplementedError
    os.chdir(settings.REPO_PATH)

    ret = subprocess.call(['svn', 'update', '--accept', 'theirs-full'])

    for filename in os.listdir(settings.REPO_PATH):
        filename = os.path.join(settings.REPO_PATH, filename)
        mtime = datetime.from_timestamp(os.stat(filename)[stat.ST_MTIME])
        	

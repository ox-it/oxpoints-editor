import os
import stat
import subprocess
import tempfile
from datetime import datetime

from lxml import etree

from django.conf import settings
from django.contrib.auth.models import User

from .models import File

class CommitFailedException(Exception):
    pass

def save_to_disk(file_obj, filename):
    xml = etree.fromstring(file_obj.xml)
    open(filename, 'w').write(etree.tostring(xml, xml_declaration=True, encoding="UTF-8"))

def perform_commit(user, message):
    os.chdir(settings.REPO_PATH)

    to_commit = set()
    for file_obj in File.objects.filter(user=user):
        filename = os.path.join(settings.REPO_PATH, file_obj.filename)
        save_to_disk(file_obj, filename)
        if not os.path.exists(filename):
            subprocess.call(['svn', 'add', filename])
        to_commit.add(file_obj)

    if not to_commit:
        return set()

    message = "%s\n\n  -- %s %s (%s)\n" % (message, user.first_name, user.last_name, user.username)

    message_file, message_filename = tempfile.mkstemp()
    try:
        os.write(message_file, message)
        os.close(message_file)
    
        for i in range(5):
            ret = subprocess.call(['svn', 'commit', '--username', settings.SVN_USER,
                                                    '--password', settings.SVN_PASSWORD,
                                                    '-F', message_filename]
                                                  + [f.filename for f in to_commit])
            if ret == 0:
                break
            to_commit -= perform_update()
        else:
            raise CommitFailedException
    finally:
        os.unlink(message_filename)

    for file_obj in to_commit:
        filename = os.path.join(settings.REPO_PATH, file_obj.filename)
        file_obj.initial_xml = file_obj.xml
        file_obj.user = None
        file_obj.last_modified = datetime.fromtimestamp(os.stat(filename)[stat.ST_MTIME])
        file_obj.save()
    
    return to_commit
    
def perform_update(force=False):
    os.chdir(settings.REPO_PATH)

    svn_proc = subprocess.Popen(['svn', 'update', '--accept', 'theirs-full'], stdout=subprocess.PIPE)
    svn_proc.wait()

    svn_updated = svn_proc.stdout.read().splitlines()
    svn_updated = set(filter(bool, [l[2:].strip() for l in svn_updated]))
    
    files = dict((f.filename, f) for f in File.objects.all())
    conflict_user = User.objects.get(username='conflict')
    filenames = set(os.listdir(settings.REPO_PATH))
    updated = set()

    for filename in filenames if force else (svn_updated & filenames):
        if not filename.endswith('.xml'):
            continue
        full_path = os.path.join(settings.REPO_PATH, filename)
        mtime = datetime.fromtimestamp(os.stat(full_path)[stat.ST_MTIME])
        
        try:
            file_obj = files[filename]
        except KeyError:
            file_obj = File(filename=filename)
            

        if file_obj.last_modified and file_obj.last_modified >= mtime:
            continue
            
        updated.add(file_obj)

        xml = etree.parse(open(full_path))
        file_obj.initial_xml = etree.tostring(xml)
        file_obj.last_modified = mtime
        
        if not file_obj.xml or not file_obj.user:
            file_obj.xml = file_obj.initial_xml

        if file_obj.user:
            file_obj.user = conflict_user

        file_obj.save()
        
    for file_obj in File.objects.all():
        if file_obj.filename not in filenames and not file_obj.user:
            file_obj.delete()
        elif file_obj.filename not in filenames:
            file_obj.initial_xml = '<empty/>'

    return updated
from django.db.models.signals import post_save

from oxpeditor.core.models import File
from oxpeditor.linkcheck.management.commands.checklinks import Command


def update_links(instance, **kwargs):
    cmd = Command()
    cmd.gather_links_for_file(instance)

post_save.connect(update_links, sender=File)

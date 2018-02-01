from django import apps


class LinkCheckConfig(apps.AppConfig):
    name = 'oxpeditor.linkcheck'

    def ready(self):
        from django.db.models.signals import post_save
        from oxpeditor.core.models import File

        post_save.connect(self.update_links, sender=File)

    def update_links(self, instance, **kwargs):
        from oxpeditor.linkcheck.management.commands.checklinks import Command
        cmd = Command()
        cmd.gather_links_for_file(instance)


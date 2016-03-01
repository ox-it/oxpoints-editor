from django.db import models

from oxpeditor.core.models import Object

STATE_CHOICES = (
    ('new', 'New'),
    ('ok', 'OK'),
    ('broken', 'Broken'),
    ('acceptable', 'Acceptable'),
)

PROBLEM_CHOICES = (
    ('new', 'New'),
    ('ok', 'OK'),
    ('url', 'URL error'),
    ('error', 'Error response'),
    ('redirect', 'Redirect'),
    ('cert', 'Certificate error'),
)

class Link(models.Model):
    object = models.ForeignKey(Object)
    type = models.CharField(max_length=64)
    target = models.URLField(max_length=2048)
    status_code = models.IntegerField(null=True, blank=True)
    redirects_to = models.URLField(max_length=2048, blank=True)
    state = models.CharField(max_length=8, choices=STATE_CHOICES, default='new')
    problem = models.CharField(max_length=8, choices=PROBLEM_CHOICES, default='new')

    last_checked = models.DateTimeField(null=True, blank=True)

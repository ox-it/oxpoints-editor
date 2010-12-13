from django.contrib import admin

from .models import Object, Relation, File

admin.site.register(Object)
admin.site.register(Relation)
admin.site.register(File)

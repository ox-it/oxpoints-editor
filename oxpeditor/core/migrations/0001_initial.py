# Generated by Django 2.0.2 on 2018-02-01 17:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.TextField()),
                ('last_modified', models.DateTimeField()),
                ('xml', models.TextField()),
                ('initial_xml', models.TextField(blank=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('filename',),
            },
        ),
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modified', models.BooleanField(default=False)),
                ('oxpid', models.CharField(max_length=8)),
                ('title', models.TextField(blank=True, null=True)),
                ('homepage', models.TextField(blank=True, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('sort_title', models.TextField(blank=True, null=True)),
                ('root_elem', models.TextField(blank=True, null=True)),
                ('type', models.TextField(blank=True, null=True)),
                ('dt_from', models.TextField(blank=True, null=True)),
                ('dt_to', models.TextField(blank=True, null=True)),
                ('idno_oucs', models.TextField(blank=True, null=True)),
                ('idno_estates', models.TextField(blank=True, null=True)),
                ('idno_finance', models.TextField(blank=True, null=True)),
                ('longitude', models.FloatField(null=True)),
                ('latitude', models.FloatField(null=True)),
                ('linking_you', models.TextField(blank=True, null=True)),
                ('autosuggest_title', models.TextField(blank=True)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('in_file', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.File')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.Object')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('sort_title', 'type'),
            },
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inferred', models.BooleanField(default=None)),
                ('type', models.CharField(choices=[('', '--------------------'), ('contains', 'contains'), ('primary', 'has primary site'), ('reception', 'has reception'), ('controls', 'has sub-unit'), ('occupies', 'occupies'), ('owns', 'owns'), ('supplies', 'supplies')], max_length=32)),
                ('active', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='active_relations', to='core.Object')),
                ('in_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.File')),
                ('passive', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passive_relations', to='core.Object')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

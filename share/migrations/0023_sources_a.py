# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-03-03 17:22
from __future__ import unicode_literals

import db.deletion
from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import share.models.ingest


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0022_system_superuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Harvester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.TextField(unique=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('long_title', models.TextField(unique=True)),
                ('home_page', models.URLField(null=True)),
                ('icon', models.ImageField(null=True, storage=share.models.ingest.SourceIconStorage(), upload_to=share.models.ingest.icon_name)),
            ],
        ),
        migrations.CreateModel(
            name='SourceConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.TextField(unique=True)),
                ('base_url', models.URLField()),
                ('earliest_date', models.DateField(null=True)),
                ('rate_limit_allowance', models.PositiveIntegerField(default=5)),
                ('rate_limit_period', models.PositiveIntegerField(default=1)),
                ('harvester_kwargs', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('transformer_kwargs', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('harvester', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='share.Harvester')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.Source')),
            ],
        ),
        migrations.CreateModel(
            name='SourceIcon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.BinaryField()),
                ('source', models.OneToOneField(on_delete=db.deletion.DatabaseOnDelete(clause='CASCADE'), to='share.Source')),
            ],
        ),
        migrations.CreateModel(
            name='SourceUniqueIdentifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.TextField()),
                ('source_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.SourceConfig')),
            ],
        ),
        migrations.CreateModel(
            name='Transformer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.TextField(unique=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='transformer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.Transformer'),
        ),
        migrations.AddField(
            model_name='source',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rawdata',
            name='suid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='share.SourceUniqueIdentifier'),
        ),
        migrations.RemoveField(
            model_name='faviconimage',
            name='user',
        ),
        migrations.RemoveField(
            model_name='shareuser',
            name='favicon',
        ),
        migrations.RemoveField(
            model_name='shareuser',
            name='home_page',
        ),
        migrations.RemoveField(
            model_name='shareuser',
            name='long_title',
        ),
        migrations.AlterUniqueTogether(
            name='sourceuniqueidentifier',
            unique_together=set([('identifier', 'source_config')]),
        ),
        migrations.DeleteModel(
            name='FaviconImage',
        ),
    ]

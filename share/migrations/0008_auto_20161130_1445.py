# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-30 14:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0007_auto_20161122_1810'),
    ]

    operations = [
        migrations.CreateModel(
            name='Retraction',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('share.publication',),
        ),
        migrations.CreateModel(
            name='RetractionVersion',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('share.publicationversion',),
        ),
        migrations.CreateModel(
            name='Retracts',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('share.workrelation',),
        ),
        migrations.CreateModel(
            name='RetractsVersion',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('share.workrelationversion',),
        ),
        migrations.AlterField(
            model_name='abstractagent',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractagentrelation',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractagentrelationversion',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractagentversion',
            name='name',
            field=models.TextField(blank=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='abstractagentversion',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractagentworkrelation',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractagentworkrelationversion',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractcreativework',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractcreativeworkversion',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractworkrelation',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='abstractworkrelationversion',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='celerytask',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterIndexTogether(
            name='change',
            index_together=set([]),
        ),
    ]
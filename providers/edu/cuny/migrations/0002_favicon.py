# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-01-17 21:31
from __future__ import unicode_literals

from django.db import migrations
import share.robot


class Migration(migrations.Migration):

    dependencies = [
        ('edu.cuny', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            code=share.robot.RobotFaviconMigration('edu.cuny'),
        ),
    ]

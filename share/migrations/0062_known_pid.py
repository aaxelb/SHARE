# Generated by Django 3.2.5 on 2022-11-23 14:06

from django.db import migrations, models
import share.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0061_ensure_auto_users'),
    ]

    operations = [
        migrations.CreateModel(
            name='KnownPid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', share.models.fields.ShareURLField(unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='sourceuniqueidentifier',
            name='focal_pid_set',
            field=models.ManyToManyField(to='share.KnownPid'),
        ),
    ]

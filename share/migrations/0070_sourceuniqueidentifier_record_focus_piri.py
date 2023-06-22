# Generated by Django 3.2.5 on 2023-06-22 15:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trove', '0001_initial'),
        ('share', '0069_rawdatum_mediatype'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourceuniqueidentifier',
            name='record_focus_piri',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='trove.persistentiri'),
        ),
    ]

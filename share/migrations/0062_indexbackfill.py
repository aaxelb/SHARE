# Generated by Django 3.2.5 on 2023-03-29 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0061_ensure_auto_users'),
    ]

    operations = [
        migrations.CreateModel(
            name='IndexBackfill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backfill_status', models.TextField(choices=[('initial', 'initial'), ('waiting', 'waiting'), ('scheduling', 'scheduling'), ('indexing', 'indexing'), ('complete', 'complete'), ('error', 'error')], default='initial')),
                ('index_strategy_name', models.TextField(unique=True)),
                ('specific_indexname', models.TextField()),
                ('error_type', models.TextField(blank=True)),
                ('error_message', models.TextField(blank=True)),
                ('error_context', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

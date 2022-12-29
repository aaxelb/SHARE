# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2021-02-23 15:54
from __future__ import unicode_literals

import datetime
from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import share.models.fields
import share.models.indexes
import share.models.ingest
import share.models.jobs
import share.models.share_user
import share.models.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0007_alter_validators_add_error_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShareUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.TextField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, validators=[django.core.validators.MaxLengthValidator(64), django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], verbose_name='username')),
                ('first_name', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(64)], verbose_name='first name')),
                ('last_name', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(64)], verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('gravatar', share.models.fields.ShareURLField(blank=True)),
                ('time_zone', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('locale', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_trusted', models.BooleanField(default=False, help_text='Designates whether the user can push directly into the db.', verbose_name='trusted')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('robot', models.TextField(blank=True, validators=[django.core.validators.MaxLengthValidator(40)])),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'Share users',
                'verbose_name': 'Share user',
            },
            managers=[
                ('objects', share.models.share_user.ShareUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='NormalizedData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('data', share.models.fields.DateTimeAwareJSONField(validators=[share.models.validators.JSONLDValidator()])),
            ],
        ),
        migrations.CreateModel(
            name='ProviderRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(0, 'pending'), (1, 'accepted'), (2, 'implemented'), (3, 'rejected')], default=0)),
                ('submitted_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('contact_name', models.TextField(max_length=300)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_affiliation', models.TextField(max_length=300)),
                ('direct_source', models.BooleanField(default=False)),
                ('source_name', models.TextField(max_length=300)),
                ('source_description', models.TextField(max_length=1000)),
                ('source_rate_limit', models.TextField(blank=True, default='', max_length=300)),
                ('source_documentation', models.TextField(blank=True, default='', max_length=300)),
                ('source_preferred_metadata_prefix', models.TextField(blank=True, default='', max_length=300)),
                ('source_oai', models.BooleanField(default=False)),
                ('source_base_url', models.URLField(blank=True, default='')),
                ('source_disallowed_sets', models.TextField(blank=True, default='', max_length=300)),
                ('source_additional_info', models.TextField(blank=True, default='', max_length=1000)),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='RawDatum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.TextField()),
                ('sha256', models.TextField(validators=[django.core.validators.MaxLengthValidator(64)])),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Raw Data',
            },
        ),
        migrations.CreateModel(
            name='SiteBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True)),
                ('color', models.IntegerField(choices=[(0, 'success'), (1, 'info'), (2, 'warning'), (3, 'danger')], default=1)),
                ('icon', models.CharField(blank=True, default='exclamation', max_length=31)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_modified_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('last_modified_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='normalizeddata',
            name='raw',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='share.RawDatum'),
        ),
        migrations.AddField(
            model_name='normalizeddata',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Harvester',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.TextField(unique=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            managers=[
                ('objects', share.models.ingest.NaturalKeyManager('key')),
            ],
        ),
        migrations.CreateModel(
            name='HarvestJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.UUIDField(null=True)),
                ('status', models.IntegerField(choices=[(0, 'Created'), (1, 'Started'), (2, 'Failed'), (3, 'Succeeded'), (4, 'Rescheduled'), (6, 'Forced'), (7, 'Skipped'), (8, 'Retrying'), (9, 'Cancelled')], db_index=True, default=0)),
                ('error_context', models.TextField(blank=True, db_column='context', default='')),
                ('completions', models.IntegerField(default=0)),
                ('date_started', models.DateTimeField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('share_version', models.TextField(default=share.models.jobs.get_share_version, editable=False)),
                ('source_config_version', models.PositiveIntegerField()),
                ('end_date', models.DateTimeField(db_index=True)),
                ('start_date', models.DateTimeField(db_index=True)),
                ('harvester_version', models.PositiveIntegerField()),
            ],
            options={
                'db_table': 'share_harvestlog',
            },
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
            managers=[
                ('objects', share.models.ingest.NaturalKeyManager('name')),
            ],
        ),
        migrations.CreateModel(
            name='SourceConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.TextField(unique=True)),
                ('version', models.PositiveIntegerField(default=1)),
                ('base_url', models.URLField(null=True)),
                ('earliest_date', models.DateField(null=True)),
                ('rate_limit_allowance', models.PositiveIntegerField(default=5)),
                ('rate_limit_period', models.PositiveIntegerField(default=1)),
                ('harvester_kwargs', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('transformer_kwargs', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('harvester', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='share.Harvester')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.Source')),
            ],
            managers=[
                ('objects', share.models.ingest.NaturalKeyManager('label')),
            ],
        ),
        migrations.CreateModel(
            name='SourceIcon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.BinaryField()),
                ('source_name', models.TextField(unique=True)),
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
            managers=[
                ('objects', share.models.ingest.NaturalKeyManager('key')),
            ],
        ),
        migrations.CreateModel(
            name='RawDatumJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datum', models.ForeignKey(db_column='rawdatum_id', on_delete=django.db.models.deletion.CASCADE, to='share.RawDatum')),
                ('job', models.ForeignKey(db_column='harvestlog_id', on_delete=django.db.models.deletion.CASCADE, to='share.HarvestJob')),
            ],
            options={
                'db_table': 'share_rawdatum_logs',
            },
        ),
        migrations.AddField(
            model_name='rawdatum',
            name='jobs',
            field=models.ManyToManyField(related_name='raw_data', through='share.RawDatumJob', to='share.HarvestJob'),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='transformer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='share.Transformer'),
        ),
        migrations.AddField(
            model_name='source',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='harvestjob',
            name='source_config',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='harvest_jobs', to='share.SourceConfig'),
        ),
        migrations.AddField(
            model_name='rawdatum',
            name='suid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.SourceUniqueIdentifier'),
        ),
        migrations.AlterUniqueTogether(
            name='sourceuniqueidentifier',
            unique_together=set([('identifier', 'source_config')]),
        ),
        migrations.AlterUniqueTogether(
            name='harvestjob',
            unique_together=set([('source_config', 'start_date', 'end_date', 'harvester_version', 'source_config_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='rawdatum',
            unique_together=set([('suid', 'sha256')]),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='earliest_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='harvester_kwargs',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='transformer_kwargs',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='harvestjob',
            name='end_date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='harvestjob',
            name='start_date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='icon',
            field=models.ImageField(blank=True, default='', storage=share.models.ingest.SourceIconStorage(), upload_to=share.models.ingest.icon_name),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='source',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='source',
            name='canonical',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.CreateModel(
            name='CeleryTaskResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correlation_id', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('FAILURE', 'FAILURE'), ('PENDING', 'PENDING'), ('RECEIVED', 'RECEIVED'), ('RETRY', 'RETRY'), ('REVOKED', 'REVOKED'), ('STARTED', 'STARTED'), ('SUCCESS', 'SUCCESS')], db_index=True, default='PENDING', max_length=50)),
                ('task_id', models.UUIDField(db_index=True, unique=True)),
                ('meta', share.models.fields.DateTimeAwareJSONField(editable=False, null=True)),
                ('result', share.models.fields.DateTimeAwareJSONField(editable=False, null=True)),
                ('task_name', models.TextField(blank=True, db_index=True, editable=False, null=True)),
                ('traceback', models.TextField(blank=True, editable=False, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('share_version', models.TextField(default=share.models.jobs.get_share_version, editable=False)),
            ],
            options={
                'verbose_name': 'Celery Task Result',
                'verbose_name_plural': 'Celery Task Results',
            },
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='full_harvest',
            field=models.BooleanField(default=False, help_text='Whether or not this SourceConfig should be fully harvested. Requires earliest_date to be set. The schedule harvests task will create all logs necessary if this flag is set. This should never be set to True by default. '),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='harvest_after',
            field=models.TimeField(default='02:00'),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='harvest_interval',
            field=models.DurationField(default='1 day'),
        ),
        migrations.AddField(
            model_name='normalizeddata',
            name='tasks',
            field=models.ManyToManyField(to='share.CeleryTaskResult'),
        ),
        migrations.AddIndex(
            model_name='celerytaskresult',
            index=models.Index(fields=['-date_modified', '-id'], name='share_celer_date_mo_686d4d_idx'),
        ),
        migrations.AddField(
            model_name='rawdatum',
            name='datestamp',
            field=models.DateTimeField(help_text="The most relevant datetime that can be extracted from this RawDatum. This may be, but is not limitted to, a deletion, modification, publication, or creation datestamp. Ideally, this datetime should be appropriate for determining the chronological order it's data will be applied.", null=True),
        ),
        migrations.CreateModel(
            name='PGLock',
            fields=[
                ('pid', models.IntegerField(primary_key=True, serialize=False)),
                ('locktype', models.TextField()),
                ('objid', models.IntegerField()),
                ('classid', models.IntegerField()),
            ],
            options={
                'db_table': 'pg_locks',
                'managed': False,
            },
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='harvest_interval',
            field=models.DurationField(default=datetime.timedelta(1)),
        ),
        migrations.CreateModel(
            name='SourceStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('response_status_code', models.SmallIntegerField(blank=True, null=True)),
                ('response_elapsed_time', models.FloatField(blank=True, null=True)),
                ('response_exception', models.TextField(blank=True, null=True)),
                ('earliest_datestamp_config', models.DateField(blank=True, null=True)),
                ('base_url_config', models.TextField()),
                ('admin_note', models.TextField(blank=True)),
                ('grade', models.FloatField()),
                ('earliest_datestamp_source', models.DateField(blank=True, null=True)),
                ('earliest_datestamps_match', models.BooleanField(default=False)),
                ('base_url_source', models.TextField(blank=True, null=True)),
                ('base_urls_match', models.BooleanField(default=False)),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.SourceConfig')),
            ],
        ),
        migrations.AddField(
            model_name='rawdatum',
            name='no_output',
            field=models.NullBooleanField(help_text='Indicates that this RawDatum resulted in an empty graph when transformed. This allows the RawDataJanitor to find records that have not been processed. Records that result in an empty graph will not have a NormalizedData associated with them, which would otherwise look like data that has not yet been processed.'),
        ),
        migrations.AddIndex(
            model_name='rawdatum',
            index=models.Index(fields=['no_output'], name='share_rawda_no_outp_f0330f_idx'),
        ),
        migrations.AlterField(
            model_name='source',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_configs', to='share.Source'),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='private_harvester_kwargs',
            field=share.models.fields.EncryptedJSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='private_transformer_kwargs',
            field=share.models.fields.EncryptedJSONField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='IngestJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.UUIDField(null=True)),
                ('status', models.IntegerField(choices=[(0, 'Created'), (1, 'Started'), (2, 'Failed'), (3, 'Succeeded'), (4, 'Rescheduled'), (6, 'Forced'), (7, 'Skipped'), (8, 'Retrying'), (9, 'Cancelled')], db_index=True, default=0)),
                ('claimed', models.NullBooleanField()),
                ('error_type', models.TextField(blank=True, db_index=True, null=True)),
                ('error_message', models.TextField(blank=True, db_column='message', null=True)),
                ('error_context', models.TextField(blank=True, db_column='context', default='')),
                ('completions', models.IntegerField(default=0)),
                ('date_started', models.DateTimeField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('share_version', models.TextField(default=share.models.jobs.get_share_version, editable=False)),
                ('source_config_version', models.PositiveIntegerField()),
                ('transformer_version', models.PositiveIntegerField()),
                ('regulator_version', models.PositiveIntegerField()),
                ('retries', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegulatorLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('node_id', models.TextField(null=True)),
                ('rejected', models.BooleanField()),
                ('ingest_job', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='regulator_logs', to='share.IngestJob')),
            ],
        ),
        migrations.AlterModelManagers(
            name='sourceconfig',
            managers=[
                ('objects', share.models.ingest.SourceConfigManager('label')),
            ],
        ),
        migrations.AddField(
            model_name='harvestjob',
            name='claimed',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='harvestjob',
            name='error_message',
            field=models.TextField(blank=True, db_column='message', null=True),
        ),
        migrations.AddField(
            model_name='harvestjob',
            name='error_type',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='rawdatum',
            name='datestamp',
            field=models.DateTimeField(help_text='The most relevant datetime that can be extracted from this RawDatum. This may be, but is not limited to, a deletion, modification, publication, or creation datestamp. Ideally, this datetime should be appropriate for determining the chronological order its data will be applied.', null=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='home_page',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='full_harvest',
            field=models.BooleanField(default=False, help_text='Whether or not this SourceConfig should be fully harvested. Requires earliest_date to be set. The schedule harvests task will create all jobs necessary if this flag is set. This should never be set to True by default. '),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='raw',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='ingest_jobs', to='share.RawDatum'),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='source_config',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='ingest_jobs', to='share.SourceConfig'),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='suid',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='ingest_jobs', to='share.SourceUniqueIdentifier'),
        ),
        migrations.AddField(
            model_name='ingestjob',
            name='ingested_normalized_data',
            field=models.ManyToManyField(related_name='ingest_jobs', to='share.NormalizedData'),
        ),
        migrations.AlterUniqueTogether(
            name='ingestjob',
            unique_together=set([('raw', 'source_config_version', 'transformer_version', 'regulator_version')]),
        ),
        migrations.AlterField(
            model_name='rawdatum',
            name='suid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='raw_data', to='share.SourceUniqueIdentifier'),
        ),
        migrations.AddField(
            model_name='sourceconfig',
            name='regulator_steps',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='FormattedMetadataRecord',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('record_format', models.TextField()),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('formatted_metadata', models.TextField()),
                ('suid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='share.SourceUniqueIdentifier')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='formattedmetadatarecord',
            unique_together=set([('suid', 'record_format')]),
        ),
        migrations.AlterField(
            model_name='formattedmetadatarecord',
            name='record_format',
            field=models.TextField(choices=[('oai_dc', 'oai_dc'), ('sharev2_elastic', 'sharev2_elastic')]),
        ),
        migrations.RunSQL(
            sql='\n                CREATE OR REPLACE FUNCTION count_estimate(query text) RETURNS INTEGER AS\n                $func$\n                DECLARE\n                    rec   record;\n                    ROWS  INTEGER;\n                BEGIN\n                    FOR rec IN EXECUTE \'EXPLAIN \' || query LOOP\n                        ROWS := SUBSTRING(rec."QUERY PLAN" FROM \' rows=([[:digit:]]+)\');\n                        EXIT WHEN ROWS IS NOT NULL;\n                    END LOOP;\n\n                    RETURN ROWS - 1;\n                END\n                $func$ LANGUAGE plpgsql;\n            ',
            reverse_sql='DROP FUNCTION count_estimate();',
        ),
    ]

import django.contrib.postgres.fields
import django.contrib.postgres.operations
import django.db.models.deletion
import django.db.models.expressions
import django.db.models.functions.text
import trove.models.resource_identifier
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ('trove', '0001_initial'),
        ('trove', '0002_indexcard_deleted'),
        ('trove', '0003_resourceidentifier_raw_iri_list'),
        ('trove', '0004_auto_20230804_2021'),
        ('trove', '0005_indexes_for_oaipmh'),
        ('trove', '0006_supplementary_indexcard_rdf'),
        ('trove', '0007_rawdata_fks_do_nothing'),
        ('trove', '0008_expiration_dates'),
        ('trove', '0009_no_raw_datum'),
        ('trove', '0010_resource_description_rename'),
        # ('trove', '0011_upgrade_django_5_2'),
    ]

    initial = True

    operations = [
        migrations.CreateModel(
            name='ResourceIdentifier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('sufficiently_unique_iri', models.TextField(unique=True, validators=[trove.models.resource_identifier.validate_sufficiently_unique_iri])),
                ('scheme_list', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(validators=[trove.models.resource_identifier.validate_iri_scheme]), size=None)),
                ('raw_iri_list', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=list, size=None)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('sufficiently_unique_iri__contains', ':'), models.Q(models.Q(('scheme_list__len__gt', 0), ('sufficiently_unique_iri__startswith', '://')), ('scheme_list', [django.db.models.functions.text.Substr('sufficiently_unique_iri', 1, django.db.models.expressions.CombinedExpression(django.db.models.functions.text.StrIndex('sufficiently_unique_iri', models.Value(':')), '-', models.Value(1)))]), _connector='OR')), name='trove_resourceidentifier_suffuniq_iri_matches_scheme_list')],
            },
        ),
        migrations.CreateModel(
            name='Indexcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('focus_identifier_set', models.ManyToManyField(related_name='indexcard_set', to='trove.resourceidentifier')),
                ('focustype_identifier_set', models.ManyToManyField(related_name='+', to='trove.resourceidentifier')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DerivedIndexcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('derived_checksum_iri', models.TextField()),
                ('derived_text', models.TextField()),
                ('deriver_identifier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='trove.resourceidentifier')),
                ('upriver_indexcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='derived_indexcard_set', to='trove.indexcard')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('upriver_indexcard', 'deriver_identifier'), name='trove_derivedindexcard_upriverindexcard_deriveridentifier')],
            },
        ),
        migrations.CreateModel(
            name='ArchivedResourceDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('turtle_checksum_iri', models.TextField(db_index=True)),
                ('focus_iri', models.TextField()),
                ('rdf_as_turtle', models.TextField()),
                ('indexcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_set', to='trove.indexcard')),
                ('expiration_date', models.DateField(blank=True, help_text='An (optional) date when this description will no longer be valid.', null=True)),
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='LatestResourceDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('turtle_checksum_iri', models.TextField(db_index=True)),
                ('focus_iri', models.TextField()),
                ('rdf_as_turtle', models.TextField()),
                ('expiration_date', models.DateField(blank=True, help_text='An (optional) date when this description will no longer be valid.', null=True)),
                ('indexcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_set', to='trove.indexcard')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('indexcard',), name='trove_latestindexcardrdf_uniq_indexcard')],
            },
        ),
        migrations.CreateModel(
            name='SupplementaryResourceDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('turtle_checksum_iri', models.TextField(db_index=True)),
                ('focus_iri', models.TextField()),
                ('rdf_as_turtle', models.TextField()),
                ('indexcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s_set', to='trove.indexcard')),
                ('expiration_date', models.DateField(blank=True, help_text='An (optional) date when this description will no longer be valid.', null=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='indexcard',
            index=models.Index(fields=['deleted'], name='trove_index_deleted_bcffde_idx'),
        ),
        migrations.AddIndex(
            model_name='latestresourcedescription',
            index=models.Index(fields=['modified'], name='trove_lates_modifie_418889_idx'),
        ),
        migrations.AddIndex(
            model_name='latestresourcedescription',
            index=models.Index(fields=['expiration_date'], name='trove_lates_expirat_70dd04_idx'),
        ),
        migrations.AddIndex(
            model_name='supplementaryresourcedescription',
            index=models.Index(fields=['expiration_date'], name='trove_suppl_expirat_3cb612_idx'),
        ),
    ]

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        # not strictly true, but keeps django's migration graph in line
        # ASSUMING all prior migrations already applied
        ('trove', '0011_upgrade_django_5_2'),
    ]

    dependencies = [
        ('trove', '1001_initial'),
        ('share', '1001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='indexcard',
            name='source_record_suid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indexcard_set', to='share.sourceuniqueidentifier'),
        ),
        migrations.AddField(
            model_name='supplementaryresourcedescription',
            name='supplementary_suid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplementary_description_set', to='share.sourceuniqueidentifier'),
        ),
        migrations.AddConstraint(
            model_name='supplementaryresourcedescription',
            constraint=models.UniqueConstraint(fields=('indexcard', 'supplementary_suid'), name='trove_supplementaryindexcardrdf_uniq_supplement'),
        ),
    ]

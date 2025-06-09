from django.db import migrations, models
from django.contrib.postgres.operations import AddIndexConcurrently


class Migration(migrations.Migration):
    atomic = False  # allow adding indexes concurrently (without locking tables)

    dependencies = [
        ('trove', '0008_expiration_dates'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='latestindexcardrdf',
            index=models.Index(fields=['expiration_date'], name='trove_lates_expirat_92ac89_idx'),
        ),
        AddIndexConcurrently(
            model_name='supplementaryindexcardrdf',
            index=models.Index(fields=['expiration_date'], name='trove_suppl_expirat_3ea6e1_idx'),
        ),
    ]

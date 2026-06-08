import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ('share', '0070_sourceuniqueidentifier_focus_identifier'),
    ]

    dependencies = [
        ('share', '1001_initial'),
        ('trove', '1001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourceuniqueidentifier',
            name='focus_identifier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='suid_set', to='trove.resourceidentifier'),
        ),
    ]

from django.conf import settings


def ensure_share_system_user(apps, schema_editor):
    ShareUser = apps.get_model('share', 'ShareUser')
    Source = apps.get_model('share', 'Source')

    system_user = ShareUser.objects.filter(username=settings.APPLICATION_USERNAME).first()
    if system_user is None:
        system_user = ShareUser.objects.create_robot_user(
            username=settings.APPLICATION_USERNAME,
            robot='',
            is_trusted=True,
        )

    Source.objects.update_or_create(
        user=system_user,
        defaults={
            'name': settings.APPLICATION_USERNAME,
            'long_title': 'SHARE System',
            'canonical': True,
        }
    )


def ensure_share_admin_user(apps, schema_editor):
    ShareUser = apps.get_model('share', 'ShareUser')
    if (
        settings.SHARE_ADMIN_USERNAME
        and settings.SHARE_ADMIN_PASSWORD
        and not ShareUser.objects.filter(username=settings.SHARE_ADMIN_USERNAME).exists()
    ):
        ShareUser.objects.create_superuser(
            settings.SHARE_ADMIN_USERNAME,
            settings.SHARE_ADMIN_PASSWORD,
        )

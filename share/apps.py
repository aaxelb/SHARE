from django.apps import AppConfig
from django.core import checks
from django.db.models.signals import post_migrate
from share.signals import ensure_latest_elastic_mappings, post_migrate_load_sources
from share.checks import check_all_index_strategies_current


class ShareConfig(AppConfig):
    name = 'share'

    def ready(self):
        post_migrate.connect(post_migrate_load_sources, sender=self)
        post_migrate.connect(ensure_latest_elastic_mappings, sender=self)
        checks.register(check_all_index_strategies_current)

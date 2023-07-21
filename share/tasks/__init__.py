import logging

import celery

from django.conf import settings
from django.db import models
from django.db import transaction

from share.harvest.scheduler import HarvestScheduler
from share import models as db
from share.search.index_messenger import IndexMessenger
from share.search.index_strategy import IndexStrategy
from share.search.messages import MessageType
from share.tasks.jobs import HarvestJobConsumer
from share.util.source_stat import SourceStatus
from share.util.source_stat import OAISourceStatus
from trove import models as trove_db


logger = logging.getLogger(__name__)


@celery.shared_task(bind=True)
def schedule_harvests(self, *source_config_ids, cutoff=None):
    """

    Args:
        *source_config_ids (int): PKs of the source configs to schedule harvests for.
            If omitted, all non-disabled and non-deleted source configs will be scheduled
        cutoff (optional, datetime): The time to schedule harvests up to. Defaults to today.

    """
    if source_config_ids:
        qs = db.SourceConfig.objects.filter(id__in=source_config_ids)
    else:
        qs = db.SourceConfig.objects.exclude(disabled=True).exclude(source__is_deleted=True)

    with transaction.atomic():
        jobs = []

        # TODO take harvest/sourceconfig version into account here
        for source_config in qs.exclude(harvester__isnull=True).select_related('harvester').annotate(latest=models.Max('harvest_jobs__end_date')):
            jobs.extend(HarvestScheduler(source_config).all(cutoff=cutoff, save=False))

        db.HarvestJob.objects.bulk_get_or_create(jobs)


@celery.shared_task(bind=True, max_retries=5)
def harvest(self, **kwargs):
    """Complete the harvest of the given HarvestJob or the next available HarvestJob.

    Keyword arguments from JobConsumer.consume, plus:
        ingest (bool, optional): Whether or not to start the full ingest process for harvested data. Defaults to True.
        limit (int, optional): Maximum number of data to harvest. Defaults to no limit.
    """
    HarvestJobConsumer(task=self).consume(**kwargs)


@celery.shared_task(bind=True)
def schedule_index_backfill(self, index_backfill_pk):
    _index_backfill = db.IndexBackfill.objects.get(pk=index_backfill_pk)
    _index_backfill.pls_note_scheduling_has_begun()
    try:
        _index_strategy = IndexStrategy.get_by_name(_index_backfill.index_strategy_name)
        _messenger = IndexMessenger(celery_app=self.app, index_strategys=[_index_strategy])
        _chunk_size = settings.ELASTICSEARCH['CHUNK_SIZE']

        def _send_messages_if_supported(messagetype, targetid_queryset):
            if messagetype in _index_strategy.supported_message_types:
                _messenger.stream_message_chunks(
                    messagetype,
                    targetid_queryset.iterator(chunk_size=_chunk_size),
                    chunk_size=_chunk_size,
                    urgent=False,
                )
        _send_messages_if_supported(MessageType.BACKFILL_INDEXCARD, (
            trove_db.Indexcard.objects
            .exclude(source_record_suid__source_config__disabled=True)
            .exclude(source_record_suid__source_config__source__is_deleted=True)
            .values_list('id', flat=True)
            .distinct()
        ))
        _send_messages_if_supported(MessageType.BACKFILL_SUID, (
            db.SourceUniqueIdentifier.objects
            .exclude(source_config__disabled=True)
            .exclude(source_config__source__is_deleted=True)
            .values_list('id', flat=True)
            .distinct()
        ))
        _send_messages_if_supported(MessageType.BACKFILL_IDENTIFIER, (
            trove_db.ResourceIdentifier.objects
            .exclude(suid_set__source_config__disabled=True)
            .exclude(suid_set__source_config__source__is_deleted=True)
            .values_list('id', flat=True)
            .distinct()
        ))
    except Exception as error:
        _index_backfill.pls_mark_error(error)
        raise error
    else:
        _index_backfill.pls_note_scheduling_has_finished()


@celery.shared_task(bind=True)
def source_stats(self):
    oai_sourceconfigs = db.SourceConfig.objects.filter(
        disabled=False,
        base_url__isnull=False,
        harvester__key='oai'
    )
    for config in oai_sourceconfigs.values():
        get_source_stats.apply_async((config['id'],))

    non_oai_sourceconfigs = db.SourceConfig.objects.filter(
        disabled=False,
        base_url__isnull=False
    ).exclude(
        harvester__key='oai'
    )
    for config in non_oai_sourceconfigs.values():
        get_source_stats.apply_async((config['id'],))


@celery.shared_task(bind=True)
def get_source_stats(self, config_id):
    source_config = db.SourceConfig.objects.get(pk=config_id)
    if source_config.harvester.key == 'oai':
        OAISourceStatus(config_id).get_source_stats()
    else:
        SourceStatus(config_id).get_source_stats()

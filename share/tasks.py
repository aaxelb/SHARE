import logging
import random

import celery

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db import transaction
from django.db import IntegrityError

from share.change import ChangeGraph
from share.harvest.exceptions import HarvesterConcurrencyError
from share.models import ChangeSet
from share.models import HarvestJob, IngestJob
from share.models import NormalizedData
from share.models import RawDatum
from share.models import Source
from share.models import SourceConfig
from share.models import CeleryTaskResult
from share.harvest.scheduler import HarvestScheduler
from share.regulate import Regulator


logger = logging.getLogger(__name__)


@celery.shared_task(bind=True)
def disambiguate(self, normalized_id):
    normalized = NormalizedData.objects.get(pk=normalized_id)
    # Load all relevant ContentTypes in a single query
    ContentType.objects.get_for_models(*apps.get_models('share'), for_concrete_models=False)

    try:
        with transaction.atomic():
            cg = ChangeGraph(normalized.data['@graph'], namespace=normalized.source.username)
            cg.process()
            cs = ChangeSet.objects.from_graph(cg, normalized.id)
            if cs and (normalized.source.is_robot or normalized.source.is_trusted or Source.objects.filter(user=normalized.source).exists()):
                # TODO: verify change set is not overwriting user created object
                cs.accept()
    except Exception as e:
        raise self.retry(
            exc=e,
            countdown=(random.random() + 1) * min(settings.CELERY_RETRY_BACKOFF_BASE ** self.request.retries, 60 * 15)
        )


@celery.shared_task(bind=True)
def schedule_harvests(self, *source_config_ids, cutoff=None):
    """

    Args:
        *source_config_ids (int): PKs of the source configs to schedule harvests for.
            If omitted, all non-disabled and non-deleted source configs will be scheduled
        cutoff (optional, datetime): The time to schedule harvests up to. Defaults to today.

    """
    if source_config_ids:
        qs = SourceConfig.objects.filter(id__in=source_config_ids)
    else:
        qs = SourceConfig.objects.exclude(disabled=True).exclude(source__is_deleted=True)

    with transaction.atomic():
        jobs = []

        # TODO take harvest/sourceconfig version into account here
        for source_config in qs.exclude(harvester__isnull=True).select_related('harvester').annotate(latest=models.Max('harvestjobs__end_date')):
            jobs.extend(HarvestScheduler(source_config).all(cutoff=cutoff, save=False))

        HarvestJob.objects.bulk_get_or_create(jobs)


@celery.shared_task(bind=True, max_retries=5)
def harvest(self, **kwargs):
    """Complete the harvest of the given HarvestJob or next the next available HarvestJob.

    Args:
        job_id (int, optional): Harvest the given job. Defaults to None.
            If the given job cannot be locked, the task will retry indefinitely.
            If the given job belongs to a disabled or deleted Source or SourceConfig, the task will fail.
        exhaust (bool, optional): Whether or not to start another harvest task if one is found. Defaults to True.
            Used to prevent a backlog of harvests. If we have a valid job, spin off another task to eat through
            the rest of the queue.
        ignore_disabled (bool, optional):
        superfluous (bool, optional): Re-ingest Rawdata that we've already collected. Defaults to False.
        force (bool, optional)


        ingest (bool, optional): Whether or not to start the full ingest process for harvested data. Defaults to True.
        limit (int, optional)
    """
    HarvestJobConsumer(self, **kwargs).consume()


@celery.shared_task(bind=True, max_retries=5)
def ingest(self, **kwargs):
    IngestJobConsumer(self, **kwargs).consume()


class JobConsumer:
    def __init__(self, task, job_id=None, exhaust=True, ignore_disabled=False, superfluous=False, force=False):
        self.task = task
        self.job_id = job_id
        self.exhaust = exhaust
        self.ignore_disabled = ignore_disabled
        self.superfluous = superfluous
        self.force = force

    @property
    def job_class(self):
        raise NotImplementedError()

    @property
    def lock_field(self):
        raise NotImplementedError()

    @property
    def task_function(self):
        raise NotImplementedError()

    def consume_job(self, job):
        raise NotImplementedError()

    def _locked_job(self):
        qs = self.job_class.objects.all()
        if self.job_id is not None:
            logger.debug('Loading %s %d', self.job_class.__name__, self.job_id)
            qs = qs.filter(id=self.job_id)
        else:
            logger.debug('job_id was not specified, searching for an available job.')

            if not self.ignore_disabled:
                qs = qs.exclude(
                    source_config__disabled=True,
                ).exclude(
                    source_config__source__is_deleted=True
                )

            qs = qs.filter(
                status__in=self.job_class.READY_STATUSES
            ).unlocked(self.lock_field)
        return qs.lock_first(self.lock_field)

    def consume(self):
        with self._locked_job() as job:
            if job is None and self.job_id is None:
                logger.warning('No %ss are currently available', self.job_class.__name__)
                return None

            if job is None and self.job_id is not None:
                # If an id was given to us, we should have gotten a job
                job = self.job_class.objects.get(id=self.job_id)  # Force the failure
                raise Exception('Failed to load {} but then found {!r}.'.format(self.job_id, job))  # Should never be reached

            if self.task.request.id:
                # Additional attributes for the celery backend
                # Allows for better analytics of currently running tasks
                self.task.update_state(meta={
                    'job_id': job.id,
                    'source': job.source_config.source.long_title,
                    'source_config': job.source_config.label,
                })

                job.task_id = self.task.request.id
                self.job_class.objects.filter(id=job.id).update(task_id=self.task.request.id)

            if job.completions > 0 and job.status == self.job_class.STATUS.succeeded:
                if not self.superfluous:
                    job.skip(self.job_class.SkipReasons.duplicated)
                    logger.warning('%r has already been harvested. Force a re-run with superfluous=True', job)
                    return None
                logger.info('%r has already been harvested. Re-running superfluously', job)

            if self.exhaust and self.job_id is None:
                if self.force:
                    logger.warning('propagating force=True until queue exhaustion')

                logger.debug('Spawning another task to consume %s', self.job_class.__name__)
                res = self.task_function.apply_async(self.task.request.args, self.task.request.kwargs)
                logger.info('Spawned %r', res)

            logger.info('Consuming %r', job)
            try:
                self.consume_job(job)
            except Exception as e:
                job.fail(e)


class HarvestJobConsumer(JobConsumer):
    job_class = HarvestJob
    lock_field = 'source_config'
    task_function = harvest

    def __init__(self, *args, limit=None, ingest=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.ingest = ingest
        self.limit = limit

    def consume_job(self, job):
        try:
            for datum in self._harvest(job):
                if self.ingest and (datum.created or self.superfluous):
                    IngestJob.schedule(datum.suid)
            if self.ingest:
                ingest.apply_async()

        except HarvesterConcurrencyError as e:
            # If job_id was specified there's a chance that the advisory lock was not, in fact, acquired.
            # If so, retry indefinitely to preserve existing functionality.
            # Use random to add jitter to help break up locking issues
            # Kinda hacky, allow a stupidly large number of retries as there is no options for infinite
            raise self.task.retry(
                exc=e,
                max_retries=99999,
                countdown=(random.random() + 1) * min(settings.CELERY_RETRY_BACKOFF_BASE ** self.task.request.retries, 60 * 15)
            )

    def _harvest(self, job):
        error = None
        datum_ids = []
        logger.info('Harvesting %r', job)
        harvester = job.source_config.get_harvester()

        with job.handle(harvester.VERSION):
            try:
                for datum in harvester.harvest_date_range(job.start_date, job.end_date, limit=self.limit, force=self.force):
                    datum_ids.append(datum.id)
                    yield datum
            except Exception as e:
                error = e
                raise error
            finally:
                try:
                    job.raw_data.add(*datum_ids)
                except Exception as e:
                    logger.exception('Failed to connect %r to raw data', job)
                    # Avoid shadowing the original error
                    if not error:
                        raise e


class IngestJobConsumer(JobConsumer):
    job_class = IngestJob
    lock_field = 'suid'
    task_function = ingest

    def consume_job(self, job):
        # TODO when partial updates are supported, get all the most recent raws back to the most recent complete update
        if job.latest_raw is None:
            job.latest_raw = RawDatum.objects.filter(suid=job.suid).order_by('-datestamp', '-date_created').first()
            if job.latest_raw is None:
                job.skip('No raw data available to ingest.')
                return

        try:
            job.save(update_fields=('latest_raw', 'date_modified'))
        except IntegrityError:
            job.latest_raw = None
            job.skip('Duplicate job exists.')
            # TODO if force or superfluous, maybe restart the other job?
            return

        transformer = job.latest_raw.suid.source_config.get_transformer()
        regulator = Regulator(job)
        with job.handle(transformer.VERSION, regulator.VERSION):
            graph = transformer.transform(job.latest_raw)
            job.log_graph('transformed_data', graph)

            if not graph:
                logger.warning('Graph was empty for %s, skipping...', job.suid)
                return

            regulator.regulate(graph)
            job.log_graph('regulated_data', graph)

            # TODO save as unmerged single-source graph

            if settings.SHARE_LEGACY_PIPELINE:
                nd = NormalizedData.objects.create(
                    data={'@graph': job.regulated_data},
                    source=job.suid.source.user,
                    raw=job.latest_raw,
                )
                nd.tasks.add(CeleryTaskResult.objects.get(task_id=self.task.request.id))

                disambiguate.apply_async((nd.id,))

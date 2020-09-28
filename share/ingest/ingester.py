import json
import uuid
import pendulum
from typing import Union

from raven.contrib.django.raven_compat.models import client as sentry_client

from share.ingest.scheduler import IngestScheduler
from share.models import RawDatum
from share.models import SourceConfig
from share.tasks import ingest
from share.tasks.jobs import IngestJobConsumer


class Ingester:
    """Helper class that takes a datum and feeds it to SHARE

    Usage given a source config:
        Ingester(datum, datum_id).with_config(source_config).ingest()

    Usage given a user and transformer:
        Ingester(datum, datum_id).as_user(user, 'transformer_key').ingest()
    """

    raw = None
    job = None
    async_task = None

    _config = None

    def __init__(self, datum: Union[str, list, dict], datum_id: str = None, datestamp=None):
        if isinstance(datum, str):
            self.datum = datum
        elif isinstance(datum, (list, dict)):
            self.datum = json.dumps(datum, sort_keys=True)
        else:
            raise TypeError('datum must be a string or a json-serializable dict or list')

        self.datum_id = datum_id or str(uuid.uuid4())
        self.datestamp = datestamp or pendulum.now()

        if not datum_id:
            sentry_client.captureMessage('Ingesting datum sans suid! This should/will be an error.', data={
                'generated_suid': self.datum_id,
            })

    def with_config(self, config):
        assert not self._config
        self._config = config
        return self

    def as_user(self, user, transformer_key='v2_push'):
        """Ingest as the given user, with the given transformer

        Create a source config for the given user/transformer, or get a previously created one.
        """
        assert not self._config
        self._config = SourceConfig.objects.get_or_create_push_config(user, transformer_key)
        return self

    def ingest(self, **kwargs):
        # "Here comes the airplane!"
        assert 'job_id' not in kwargs
        self._setup_ingest(claim_job=True)
        IngestJobConsumer().consume(job_id=self.job.id, exhaust=False, **kwargs)
        return self

    def ingest_async(self, start_task=True, **kwargs):
        # "There's pizza in the fridge."
        assert 'job_id' not in kwargs
        self._setup_ingest(claim_job=start_task)
        if start_task:
            self.async_task = ingest.delay(job_id=self.job.id, exhaust=False, **kwargs)
        return self

    def _setup_ingest(self, claim_job):
        assert self.datum and self._config and not (self.raw or self.job or self.async_task)

        # TODO get rid of FetchResult, or make it more sensical
        from share.harvest.base import FetchResult
        fetch_result = FetchResult(self.datum_id, self.datum, self.datestamp)
        self.raw = RawDatum.objects.store_data(self._config, fetch_result)
        self.job = IngestScheduler().schedule(self.raw.suid, self.raw.id, claim=claim_job)

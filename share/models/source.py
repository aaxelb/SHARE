import contextlib
import datetime
import logging

from django.db import connections
from django.db import models

from share.models.fields import EncryptedJSONField
from share.util import BaseJSONAPIMeta


logger = logging.getLogger(__name__)
__all__ = ('Source', 'SourceConfig', )


class Source(models.Model):
    domain = models.TextField(unique=True)
    home_page = models.URLField(null=True, blank=True)

    # Whether or not this SourceConfig collects original content
    # If True changes made by this source cannot be overwritten
    # This should probably be on SourceConfig but placing it on Source
    # is much easier for the moment.
    # I also haven't seen a situation where a Source has two feeds that we harvest
    # where one provider unreliable metadata but the other does not.
    canonical = models.BooleanField(default=False, db_index=True)

    # TODO replace with object permissions, allow multiple sources per user (SHARE-996)
    user = models.OneToOneField('ShareUser', null=True, on_delete=models.CASCADE)

    class JSONAPIMeta(BaseJSONAPIMeta):
        pass

    def natural_key(self):
        return (self.name,)

    def __repr__(self):
        return '<{}({}, {}, {})>'.format(self.__class__.__name__, self.pk, self.name, self.long_title)

    def __str__(self):
        return repr(self)


class SourceConfig(models.Model):
    # Previously known as the provider's app_label
    label = models.TextField(unique=True)
    version = models.PositiveIntegerField(default=1)

    source = models.ForeignKey('Source', on_delete=models.CASCADE, related_name='source_configs')
    base_url = models.URLField(null=True)
    earliest_date = models.DateField(null=True, blank=True)
    rate_limit_allowance = models.PositiveIntegerField(default=5)
    rate_limit_period = models.PositiveIntegerField(default=1)

    # Allow null for push sources
    harvester = models.ForeignKey('Harvester', null=True, on_delete=models.CASCADE)
    harvester_kwargs = models.JSONField(null=True, blank=True)
    harvest_interval = models.DurationField(default=datetime.timedelta(days=1))
    harvest_after = models.TimeField(default='02:00')
    full_harvest = models.BooleanField(default=False, help_text=(
        'Whether or not this SourceConfig should be fully harvested. '
        'Requires earliest_date to be set. '
        'The schedule harvests task will create all jobs necessary if this flag is set. '
        'This should never be set to True by default. '
    ))

    # Allow null for push sources
    # TODO put pushed data through a transformer, add a JSONLDTransformer or something for backward compatibility
    transformer = models.ForeignKey('Transformer', null=True, on_delete=models.CASCADE)
    transformer_kwargs = models.JSONField(null=True, blank=True)

    regulator_steps = models.JSONField(null=True, blank=True)

    disabled = models.BooleanField(default=False)

    private_harvester_kwargs = EncryptedJSONField(blank=True, null=True)
    private_transformer_kwargs = EncryptedJSONField(blank=True, null=True)

    def get_harvester(self, **kwargs):
        """Return a harvester instance configured for this SourceConfig.

        **kwargs: passed to the harvester's initializer
        """
        return self.harvester.get_class()(self, **kwargs)

    def get_transformer(self, **kwargs):
        """Return a transformer instance configured for this SourceConfig.

        **kwargs: passed to the transformer's initializer
        """
        return self.transformer.get_class()(self, **kwargs)

    @contextlib.contextmanager
    def acquire_lock(self, required=True, using='default'):
        from share.harvest.exceptions import HarvesterConcurrencyError

        # NOTE: Must be in transaction
        logger.debug('Attempting to lock %r', self)
        with connections[using].cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s::regclass::integer, %s);", (self._meta.db_table, self.id))
            locked = cursor.fetchone()[0]
            if not locked and required:
                logger.warning('Lock failed; another task is already harvesting %r.', self)
                raise HarvesterConcurrencyError('Unable to lock {!r}'.format(self))
            elif locked:
                logger.debug('Lock acquired on %r', self)
            else:
                logger.warning('Lock not acquired on %r', self)
            try:
                yield
            finally:
                if locked:
                    cursor.execute("SELECT pg_advisory_unlock(%s::regclass::integer, %s);", (self._meta.db_table, self.id))
                    logger.debug('Lock released on %r', self)

    def __repr__(self):
        return '<{}({}, {})>'.format(self.__class__.__name__, self.pk, self.label)

    __str__ = __repr__

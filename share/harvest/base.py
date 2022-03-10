import abc
import datetime
import logging
import types
import warnings

import pendulum
import requests

from django.conf import settings
from django.utils import timezone

from share.harvest.ratelimit import RateLimittedProxy
from share.harvest.serialization import DeprecatedDefaultSerializer
from share.models.metadata_representation import MetadataRepresentation


logger = logging.getLogger(__name__)


class BaseHarvester(metaclass=abc.ABCMeta):
    # TODO-quest: no store! only fetch
    """
    Politely fetch metadata from remote sources.
    """

    SERIALIZER_CLASS = DeprecatedDefaultSerializer

    network_read_timeout = 30
    network_connect_timeout = 31

    @property
    def request_timeout(self):
        """The timeout tuple for requests (connect, read)
        """
        return (self.network_connect_timeout, self.network_read_timeout)

    def __init__(self, source_config, network_read_timeout=None, network_connect_timeout=None):
        """

        Args:
            source_config (SourceConfig):

        """
        self.config = source_config
        self.serializer = self.SERIALIZER_CLASS()

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': settings.SHARE_USER_AGENT})
        # TODO Make rate limit apply across threads
        self.requests = RateLimittedProxy(self.session, self.config.rate_limit_allowance, self.config.rate_limit_period)

        self.network_read_timeout = (network_read_timeout or self.network_read_timeout)
        self.network_connect_timeout = (network_connect_timeout or self.network_connect_timeout)

    def fetch_by_id(self, identifier, **kwargs):
        datum = self._do_fetch_by_id(identifier, **self._get_kwargs(**kwargs))
        return MetadataRepresentation(
            object_url=identifier,  # TODO-quest: guarantee url in harvester
            content=self.serializer.serialize(datum),
        )

    def _do_fetch_by_id(self, identifier, **kwargs):
        """Fetch a document by provider ID.

        Optional to implement, intended for dev and manual testing.

        Args:
            identifier (str): Unique ID the provider uses to identify works.

        Returns:
            FetchResult

        """
        raise NotImplementedError('{!r} does not support fetching by ID'.format(self))

    def fetch(self, today=False, **kwargs):
        """Fetch data from today.

        Yields:
            FetchResult

        """
        return self.fetch_date_range(datetime.date.today() - datetime.timedelta(days=1), datetime.date.today(), **kwargs)

    def fetch_date(self, date: datetime.date, **kwargs):
        """Fetch data from the specified date.

        Yields:
            FetchResult
        """
        return self.fetch_date_range(date - datetime.timedelta(days=1), date, **kwargs)

    def fetch_date_range(self, start, end, limit=None, **kwargs):
        """Fetch data from the specified date range.

        Yields:
            FetchResult

        """
        # TODO-quest: either use `with self.config.acquire_lock(required=not force):`
        #             or delete `SourceConfig.acquire_lock` and friends

        if not isinstance(start, datetime.date):
            raise TypeError('start must be a datetime.date. Got {!r}'.format(start))

        if not isinstance(end, datetime.date):
            raise TypeError('end must be a datetime.date. Got {!r}'.format(end))

        if start >= end:
            raise ValueError('start must be before end. {!r} > {!r}'.format(start, end))

        if limit == 0:
            return  # No need to do anything

        # Cast to datetimes for compat reasons
        start = pendulum.instance(datetime.datetime.combine(start, datetime.time(0, 0, 0, 0, timezone.utc)))
        end = pendulum.instance(datetime.datetime.combine(end, datetime.time(0, 0, 0, 0, timezone.utc)))

        if hasattr(self, 'shift_range'):
            warnings.warn(
                '{!r} implements a deprecated interface. '
                'Handle date transforms in _do_fetch. '
                'shift_range will no longer be called in SHARE 2.9.0'.format(self),
                DeprecationWarning
            )
            start, end = self.shift_range(start, end)

        data_gen = self._do_fetch(start, end, **self._get_kwargs(**kwargs))

        if not isinstance(data_gen, types.GeneratorType) and len(data_gen) != 0:
            raise TypeError('{!r}._do_fetch must return a GeneratorType for optimal performance and memory usage'.format(self))

        for i, blob in enumerate(data_gen):
            result = MetadataRepresentation(
                object_url=blob[0],
                representation_content=self.serializer.serialize(blob[1]),
                # TODO-quest: source timestamp?
            )

            if result.datestamp is None:
                result.datestamp = start
            elif (result.datestamp.date() < start.date() or result.datestamp.date() > end.date()):
                if (start - result.datestamp) > pendulum.Duration(hours=24) or (result.datestamp - end) > pendulum.Duration(hours=24):
                    raise ValueError(
                        'result.datestamp is outside of the requested date range. '
                        '{} from {} is not within [{} - {}]'.format(result.datestamp, result.identifier, start, end)
                    )
                logger.warning(
                    'result.datestamp is within 24 hours of the requested date range. '
                    'This is probably a timezone conversion error and will be accepted. '
                    '{} from {} is within 24 hours of [{} - {}]'.format(result.datestamp, result.identifier, start, end)
                )

            yield result

            if limit is not None and i >= limit:
                break

    def _do_fetch(self, start, end, **kwargs):
        """Fetch date from this source inside of the given date range.

        The given date range should be treated as [start, end)

        Any HTTP[S] requests MUST be sent using the self.requests client.
        It will automatically enforce rate limits

        Args:
            start_date (datetime): Date to start fetching data from, inclusively.
            end_date (datetime): Date to fetch data up to, exclusively.
            **kwargs: Arbitrary kwargs passed to subclasses, used to customize harvesting. Overrides values in the source config's harvester_kwargs.

        Returns:
            Iterator<FetchResult>: The fetched data.

        """
        if hasattr(self, 'do_harvest'):
            warnings.warn(
                '{!r} implements a deprecated interface. '
                'do_harvest has been replaced by _do_fetch for clarity. '
                'do_harvest will no longer be called in SHARE 2.11.0'.format(self),
                DeprecationWarning
            )
            logger.warning('%r implements a deprecated interface. ', self)
            return self.do_harvest(start, end, **kwargs)

        raise NotImplementedError()

    def _get_kwargs(self, **kwargs):
        return {**(self.config.harvester_kwargs or {}), **kwargs}

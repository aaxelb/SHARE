from hashlib import sha256
from django.db import models

from trove.util import simple___repr__


class MetadataExpression(models.Model):
    __repr__ = simple___repr__(
        'url_to_the_thing',
        'raw_mediatype',
        'raw_hash',
    )

    id = models.AutoField(primary_key=True)  # db-internal id only
    local_timestamp = models.DateTimeField(auto_now=True)

    # I'm talking about *the thing*! That thing over there! This URL is a map to find it! Do you see?
    # (tho if the thing is anywhere beside digitalspace, might still only get info about it)
    # TODO-quest: validate URL
    url_to_the_thing = models.URLField()

    #  HTTP Content-Type header (https://httpwg.org/specs/rfc7231.html#header.content-type)
    # (unrelated to django.contrib.contenttypes)
    # TODO-quest: validation? or let 'em be wild?
    raw_mediatype = models.TextField()

    # TODO-quest: also embrace HTTP's Language and Encoding headers?
    # language = models.TextField()
    # encoding = models.TextField()

    # content could be JSON, XML, text, audio, image, video...
    # TODO-quest: reasonable size limit (probably some few kilobytes)
    raw = models.BinaryField()

    # assumed sha256 (...for now)
    # TODO-quest: auto-compute hash on save -- in model or db trigger
    raw_hash = models.CharField(max_length=64)

    # TODO-quest: consider how to answer "whois the one who gave us this?"

    class Meta:
        constraints = [
            # TODO-quest: consider how to handle "same metadata for multiple URLs"
            models.UniqueConstraint(fields=['raw_hash'], name='unique_by_raw_hash'),
        ]
        indexes = [
            # for getting all metadata expressions about a thing (given its URL)
            models.Index(fields=['url_to_the_thing'], name='index_by_url_to_the_thing'),

            # for "feeds" of recent expressions filtered by mediatype
            models.Index(fields=['raw_mediatype', '-local_timestamp'], name='index_by_recent_mediatype'),
        ]

    def compute_raw_hash(self):
        self.raw_hash = sha256(self.raw).hexdigest()

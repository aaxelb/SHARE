from hashlib import sha256
from django.db import models

from trove.util import simple___repr__


class MetadataExpression(models.Model):
    __repr__ = simple___repr__(
        'url_to_the_thing',
        'mediatype',
        'hashed_expression',
    )

    id = models.AutoField(primary_key=True)  # db-internal id only
    local_timestamp = models.DateTimeField(auto_now=True)

    # I'm talking about *the thing*! That thing over there! This URL is a map to find it! Do you see?
    #   (tho if the thing is anywhere beside digitalspace, might still only get info about it)
    # TODO-quest: validate URL
    url_to_the_thing = models.URLField()

    # same as the HTTP Content-Type header (https://httpwg.org/specs/rfc7231.html#header.content-type)
    # (unrelated to django.contrib.contenttypes)
    # TODO-quest: validation? or let 'em be wild?
    mediatype = models.TextField()

    # TODO-quest: also embrace HTTP's Language and Encoding headers?
    # language = models.TextField()
    # encoding = models.TextField()

    # content could be JSON, XML, text, audio, image, video...
    # TODO-quest: reasonable size limit (probably some few kilobytes)
    raw_expression = models.BinaryField()

    # assumed sha256 (...for now)
    # TODO-quest: auto-compute hash on save -- in model or db trigger
    hashed_expression = models.CharField(max_length=64)

    # TODO-quest: using harvest_job would make it complicated to answer "who gave us this?"
    #             self.harvest_job.source_config.source.user... consider improvements
    # harvest_job = models.ForeignKey('HarvestJob', null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            # TODO-quest: consider how to handle "same metadata for multiple URLs"
            models.UniqueConstraint(fields=['hashed_expression'], name='unique_by_hashed_expression'),
        ]
        indexes = [
            models.Index(fields=['url_to_the_thing'], name='index_by_url_to_the_thing'),
            models.Index(fields=['mediatype', '-local_timestamp'], name='index_by_recent_mediatype'),
        ]

    def compute_hash(self):
        self.hashed_expression = sha256(self.raw_expression).hexdigest()

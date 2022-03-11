from hashlib import sha256
from django.db import models

from share.util import simple___repr__


class MetadataExpression(models.Model):
    __repr__ = simple___repr__(
        'object_url',
        'content_type',
        'content_hash',
    )

    id = models.AutoField(primary_key=True)  # db-internal id only
    local_timestamp = models.DateTimeField(auto_now=True)

    # the thing! that thing over there! here's a map to find it!
    # (let's agree to use identifiers that also locate -- *URL*, not just URI)
    # (tho if the thing is anywhere besides digitalspace, might be you still only get info about it)
    object_url = models.URLField()

    # used for HTTP Content-Type header (https://httpwg.org/specs/rfc7231.html#header.content-type)
    # (unrelated to django.contrib.contenttypes, probably)
    # TODO-quest: validation? choices? size limit?
    content_type = models.TextField()

    # TODO-quest:
    # content_language = models.TextField()
    # content_encoding = models.TextField()

    # content could be JSON, XML, text, audio, image, video...
    # TODO-quest: reasonable size limit (probably some few kilobytes)
    content = models.FileField()

    # assumed sha256 (...for now)
    # TODO-quest: auto-compute hash on save -- in model or db trigger
    content_hash = models.CharField(max_length=64, min_length=64)

    # TODO-quest: so complicated to answer "who gave us this?"
    #             self.harvest_job.source_config.source.user...
    #             consider improvement
    harvest_job = models.ForeignKey('HarvestJob', null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['content_hash']),
        ]
        indexes = [
            models.Index(fields=['object_url']),
            models.Index(fields=['content_type', '-local_timestamp']),
        ]

    def compute_content_hash(self):
        self.content_hash = sha256(self.content).hexdigest()

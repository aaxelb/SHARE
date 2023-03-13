from django.db import models


class IndexBackfillStatus(models.Model):
    INITIATED = 'initiated'
    ENQUEUING = 'enqueuing'
    INDEXING = 'indexing'
    COMPLETE = 'complete'
    BACKFILL_STATUS_CHOICES = (
        (INITIATED, INITIATED),
        (ENQUEUING, ENQUEUING),
        (INDEXING, INDEXING),
        (COMPLETE, COMPLETE),
    )
    backfill_status = models.TextField(choices=BACKFILL_STATUS_CHOICES, default=INITIATED)
    index_strategy_name = models.TextField(unique=True)
    specific_index_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

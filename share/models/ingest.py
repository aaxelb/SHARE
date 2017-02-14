from stevedore import driver
from django.contrib.postgres.fields import JSONField
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.deconstruct import deconstructible

from db.deletion import DATABASE_CASCADE

from share.models.fuzzycount import FuzzyCountManager

__all__ = ('Source', 'SourceConfig', 'Harvester', 'Transformer')


class SourceIcon(models.Model):
    source = models.OneToOneField('Source', on_delete=DATABASE_CASCADE)
    image = models.BinaryField()


@deconstructible
class SourceIconStorage(Storage):
    def _open(self, name, mode='rb'):
        assert mode == 'rb'
        icon = SourceIcon.objects.get(source__name=name)
        return ContentFile(icon.image)

    def _save(self, name, content):
        source = Source.objects.get(name=name)
        SourceIcon.objects.update_or_create(source_id=source.id, defaults={'image': content.read()})
        return name

    def delete(self, name):
        SourceIcon.objects.get(source__name=name).delete()

    def get_available_name(self, name, max_length=None):
        return name

    def url(self, name):
        return reverse('source_icon', kwargs={'source_name': name})


def icon_name(instance, filename):
    return instance.name


class NaturalKeyManager(FuzzyCountManager):
    def __init__(self, *key_fields):
        super(NaturalKeyManager, self).__init__()
        self.key_fields = key_fields

    def get_by_natural_key(self, key):
        return self.get(**dict(zip(self.key_fields, key)))


class Source(models.Model):
    name = models.TextField(unique=True)
    long_title = models.TextField(unique=True)
    home_page = models.URLField(null=True)
    icon = models.ImageField(upload_to=icon_name, storage=SourceIconStorage(), null=True)

    # TODO replace with Django permissions something something, allow multiple sources per user
    user = models.OneToOneField('ShareUser')

    objects = NaturalKeyManager('name')

    def natural_key(self):
        return (self.name,)


class SourceConfig(models.Model):
    # Previously known as the provider's app_label
    label = models.TextField(unique=True)

    source = models.ForeignKey('Source')
    base_url = models.URLField()
    earliest_date = models.DateField(null=True)
    rate_limit_allowance = models.PositiveIntegerField(default=5)
    rate_limit_period = models.PositiveIntegerField(default=1)

    harvester = models.ForeignKey('Harvester', null=True)
    harvester_kwargs = JSONField(null=True)

    transformer = models.ForeignKey('Transformer')
    transformer_kwargs = JSONField(null=True)

    disabled = models.BooleanField(default=False)

    objects = NaturalKeyManager('label')

    def natural_key(self):
        return (self.label,)

    def get_harvester(self):
        return self.harvester.get_class()(self, **(self.harvester_kwargs or {}))

    def get_transformer(self):
        return self.transformer.get_class()(self, **(self.transformer_kwargs or {}))


class Harvester(models.Model):
    key = models.TextField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = NaturalKeyManager('key')

    def natural_key(self):
        return (self.key,)

    def get_class(self):
        return driver.DriverManager('share.harvesters', self.key).driver

    @property
    def version(self):
        return self.get_class().VERSION


class Transformer(models.Model):
    key = models.TextField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = NaturalKeyManager('key')

    def natural_key(self):
        return (self.key,)

    def get_class(self):
        return driver.DriverManager('share.transformers', self.key).driver

    @property
    def version(self):
        return self.get_class().VERSION

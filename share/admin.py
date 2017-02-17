import ast
import datetime
import importlib

import celery

from django.apps import apps
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from oauth2_provider.models import AccessToken
from django.utils import timezone
from django.contrib.admin.views.main import ChangeList

from share.robot import RobotAppConfig
from share.models.celery import CeleryTask
from share.models.change import ChangeSet
from share.models.core import NormalizedData, ShareUser
from share.models.ingest import RawDatum, Source, SourceConfig, Harvester, Transformer
from share.models.logs import HarvestLog
from share.models.registration import ProviderRegistration
from share.models.banner import SiteBanner
from share.readonlyadmin import ReadOnlyAdmin


class NormalizedDataAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_filter = ['source', ]
    raw_id_fields = ('raw', 'tasks',)


class ChangeSetSubmittedByFilter(SimpleListFilter):
    title = 'Source'
    parameter_name = 'source_id'

    def lookups(self, request, model_admin):
        return ShareUser.objects.filter(is_active=True).values_list('id', 'username')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(normalized_data__source_id=self.value())
        return queryset


class ChangeSetAdmin(admin.ModelAdmin):
    list_display = ('status_', 'count_changes', 'submitted_by', 'submitted_at')
    actions = ['accept_changes']
    list_filter = ['status', ChangeSetSubmittedByFilter]
    raw_id_fields = ('normalized_data',)

    def submitted_by(self, obj):
        return obj.normalized_data.source
    submitted_by.short_description = 'submitted by'

    def count_changes(self, obj):
        return obj.changes.count()
    count_changes.short_description = 'number of changes'

    def status_(self, obj):
        return ChangeSet.STATUS[obj.status].title()


class AppLabelFilter(admin.SimpleListFilter):
    title = 'App Label'
    parameter_name = 'app_label'

    def lookups(self, request, model_admin):
        return sorted([
            (config.label, config.label)
            for config in apps.get_app_configs()
            if isinstance(config, RobotAppConfig)
        ])

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(app_label=self.value())
        return queryset


class TaskNameFilter(admin.SimpleListFilter):
    title = 'Task'
    parameter_name = 'task'

    def lookups(self, request, model_admin):
        return sorted(
            (key, key)
            for key in celery.current_app.tasks.keys()
            if key.startswith('share.')
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name=self.value())
        return queryset


class CeleryTaskChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        return ['-timestamp']


class CeleryTaskAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'name', 'status', 'provider', 'app_label', 'started_by')
    actions = ['retry_tasks']
    list_filter = ['status', TaskNameFilter, AppLabelFilter, 'started_by']
    list_select_related = ('provider', 'started_by')
    fields = (
        ('app_label', 'app_version'),
        ('started_by', 'provider'),
        ('uuid', 'name'),
        ('args', 'kwargs'),
        'timestamp',
        'status',
        'traceback',
    )
    readonly_fields = ('name', 'uuid', 'args', 'kwargs', 'status', 'app_version', 'app_label', 'timestamp', 'status', 'traceback', 'started_by', 'provider')

    def traceback(self, task):
        return apps.get_model('djcelery', 'taskmeta').objects.filter(task_id=task.uuid).first().traceback

    def get_changelist(self, request, **kwargs):
        return CeleryTaskChangeList

    def retry_tasks(self, request, queryset):
        for task in queryset:
            task_id = str(task.uuid)
            parts = task.name.rpartition('.')
            Task = getattr(importlib.import_module(parts[0]), parts[2])
            if task.app_label:
                args = (task.started_by.id, task.app_label) + ast.literal_eval(task.args)
            else:
                args = (task.started_by.id,) + ast.literal_eval(task.args)
            kwargs = ast.literal_eval(task.kwargs)
            Task().apply_async(args, kwargs, task_id=task_id)
    retry_tasks.short_description = 'Retry tasks'


class AbstractCreativeWorkAdmin(admin.ModelAdmin):
    list_display = ('type', 'title', 'num_contributors')
    list_filter = ['type']
    raw_id_fields = ('change', 'extra', 'extra_version', 'same_as', 'same_as_version', 'subjects')

    def num_contributors(self, obj):
        return obj.contributors.count()
    num_contributors.short_description = 'Contributors'


class AbstractAgentAdmin(admin.ModelAdmin):
    list_display = ('type', 'name')
    list_filter = ('type',)
    raw_id_fields = ('change', 'extra', 'extra_version', 'same_as', 'same_as_version',)


class TagAdmin(admin.ModelAdmin):
    raw_id_fields = ('change', 'extra', 'extra_version', 'same_as', 'same_as_version',)


class RawDatumAdmin(admin.ModelAdmin):
    raw_id_fields = ()


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'scope')


class ProviderRegistrationAdmin(ReadOnlyAdmin):
    list_display = ('source_name', 'status_', 'submitted_at', 'submitted_by', 'direct_source')
    list_filter = ('direct_source', 'status',)
    readonly_fields = ('submitted_at', 'submitted_by',)

    def status_(self, obj):
        return ProviderRegistration.STATUS[obj.status].title()


class SiteBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'color', 'icon', 'active')
    list_editable = ('active',)
    ordering = ('-active', '-last_modified_at')
    readonly_fields = ('created_at', 'created_by', 'last_modified_at', 'last_modified_by')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class SourceConfigFilter(admin.SimpleListFilter):
    title = 'Source Config'
    parameter_name = 'source_config'

    def lookups(self, request, model_admin):
        # TODO make this into a cool hierarchy deal
        # return SourceConfig.objects.select_related('source').values_list('
        return SourceConfig.objects.order_by('label').values_list('id', 'label')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_config=self.value())


class HarvestLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'label', 'share_version', 'status_', 'start_date_', 'end_date_', )
    list_filter = ('status', SourceConfigFilter, )
    list_select_related = ('source_config__source', )

    def source(self, obj):
        return obj.source_config.source.long_title

    def label(self, obj):
        return obj.source_config.label

    def start_date_(self, obj):
        return obj.start_date.date().isoformat()

    def end_date_(self, obj):
        return obj.end_date.date().isoformat()

    def status_(self, obj):
        if obj.status == HarvestLog.STATUS.created and (timezone.now() - obj.date_modified) > datetime.timedelta(minutes=60):
            return '<span style="font-weight: bold;">Lost</span>'
        return '<span style="font-weight: bold; color: {}">{}</span>'.format(
            ['blue', 'cyan', 'red', 'green', 'goldenrod', 'orange'][obj.status],
            HarvestLog.STATUS[obj.status].title(),
        )

    status_.allow_tags = True


admin.site.unregister(AccessToken)
admin.site.register(AccessToken, AccessTokenAdmin)

admin.site.register(CeleryTask, CeleryTaskAdmin)
admin.site.register(ChangeSet, ChangeSetAdmin)
admin.site.register(HarvestLog, HarvestLogAdmin)
admin.site.register(NormalizedData, NormalizedDataAdmin)
admin.site.register(ProviderRegistration, ProviderRegistrationAdmin)
admin.site.register(RawDatum, RawDatumAdmin)
admin.site.register(SiteBanner, SiteBannerAdmin)

admin.site.register(Harvester)
admin.site.register(ShareUser)
admin.site.register(Source)
admin.site.register(SourceConfig)
admin.site.register(Transformer)

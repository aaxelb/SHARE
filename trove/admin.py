from django.contrib import admin

from trove.models.metadata_expression import MetadataExpression


class MetadataExpressionAdmin(admin.ModelAdmin):
    pass


admin.site.register(MetadataExpression, MetadataExpressionAdmin)

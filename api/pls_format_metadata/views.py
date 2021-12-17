import json

from django.http import HttpResponse

from share.util.extensions import Extensions
from share.regulate import Regulator


def pls_format_metadata(request):
    if request.method != 'POST':
        return HttpResponse(
            status=405,
            headers={'Allow': 'POST'},
            content='only POST!'
        )

    transformer_key = request.GET.get('transformer', 'v2_push')
    normal_graph = pls_normalize(request.body, transformer_key)
    requested_formats = request.GET.getlist('formats')
    formatted_records = [
        pls_format(normal_graph, format_key)
        for format_key in requested_formats
    ]
    return HttpResponse(
        content=json.dumps(formatted_records),
    )


def pls_normalize(raw_datum, transformer_key):
    transformer = Extensions.get('share.transformers', transformer_key)()
    graph = transformer.transform(raw_datum)
    Regulator().regulate(graph)  # in-place


def pls_format(graph, record_formats):
    formatters = [
        Extensions.get('share.metadata_formats', record_format)()
        for record_format in record_formats
    ]
    return [
        formatter.format_from_graph(graph)
        for formatter in formatters
    ]

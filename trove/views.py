
from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from trove.models.metadata_expression import MetadataExpression


async def expression_basket(request, object_url):
    if request.method == 'GET':
        expression_basket = await get_expression_basket(object_url)
        # TODO-quest: HTML page
        return HttpResponse(expression_basket)

    if request.method == 'PUT':
        await put_expression_in_basket(
            object_url=object_url,
            content_type=request.headers['Content-Type'],
            content=request.body,
        )
        # TODO-quest: helpful response body
        return HttpResponse(status='201')

    raise NotImplementedError


@sync_to_async
def get_expression_basket(object_url):
    expression_qs = (
        MetadataExpression.objects
        .filter(object_url=object_url)
        .values(
            'content_type',
            'content_hash',
            # TODO-quest: url for expression_basket
        )
    )
    return '\n'.join(
        f"{v['content_type']}: {v['content_hash']}"
        for v in expression_qs
    )


@sync_to_async
def put_expression_in_basket(object_url, content_type, content):
    # TODO-quest auth

    expression = MetadataExpression(
        object_url=object_url,
        content_type=content_type,
        content=content,
    )
    expression.compute_content_hash()
    expression.save()
    return HttpResponse(status=201)


async def expression(request, content_hash):
    if request.method == 'GET':
        try:
            md_expression = MetadataExpression.objects.get(content_hash=content_hash)
            return HttpResponse(
                content_type=md_expression.content_type,
                body=md_expression.content,
            )
        except MetadataExpression.DoesNotExist:
            return HttpResponse(status=404)

    raise NotImplementedError


async def feed(request, content_type):
    # TODO-quest: pagination (cursor)
    # TODO-quest: maybe allow wildcard content_types like 'text/*', '*/*'

    expression_feed_qs = (
        MetadataExpression.objects
        .filter(content_type=content_type)
        .values(
            'object_url',
            'content_type',
            'content_hash',
        )
    )

    # TODO-quest: json:api
    response_body = [
        {
            **expression_values,
            'content_url': reverse('trove:expression', kwargs={
                'content_hash': expression_values['content_hash'],
            }),
        }
        for expression_values in expression_feed_qs
    ]
    return JsonResponse(response_body)

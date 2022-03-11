
from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from trove.models.metadata_expression import MetadataExpression


# TODO-quest: html, when acceptable
# TODO-quest: json:api, when acceptable


async def mediatype_basket(request):
    if request.method == 'GET':
        mediatypes = await get_all_mediatypes()
        return JsonResponse({'mediatype-basket': mediatypes})
    raise NotImplementedError


@sync_to_async
def get_all_mediatypes():
    return list(
        MetadataExpression.objects
        .values_list('mediatype', flat=True)
        .distinct('mediatype')
    )


async def expression_basket(request, url_to_the_thing):
    if request.method == 'GET':
        expression_basket = await get_expression_basket(url_to_the_thing)
        return JsonResponse({'expression-basket': expression_basket})

    if request.method == 'PUT':
        await put_expression_into_basket(
            url_to_the_thing=url_to_the_thing,
            mediatype=request.headers['Content-Type'],
            raw=request.body,
        )
        expression_basket = await get_expression_basket(url_to_the_thing)
        return JsonResponse(
            {'expression-basket': expression_basket},
            status=201,
        )

    raise NotImplementedError


@sync_to_async
def get_expression_basket(url_to_the_thing):
    expression_qs = (
        MetadataExpression.objects
        .filter(url_to_the_thing=url_to_the_thing)
        .values(
            'mediatype',
            'raw_hash',
        )
    )

    return [
        {
            'mediatype': v['mediatype'],
            'raw_hash': v['raw_hash'],
            'url-to-raw-expression': reverse('trove:raw-expression', kwargs={
                'raw-hash': v['raw_hash'],
            }),
        }
        for v in expression_qs
    ]


@sync_to_async
def put_expression_into_basket(url_to_the_thing, mediatype, raw_expression):
    # TODO-quest: auth

    expression = MetadataExpression(
        url_to_the_thing=url_to_the_thing,
        mediatype=mediatype,
        raw=raw_expression,
    )
    expression.compute_raw_hash()
    expression.save()
    return HttpResponse(status=201)


async def raw_expression(request, raw_hash):
    if request.method == 'GET':
        try:
            expression = await get_expression(raw_hash)
            return HttpResponse(
                content=expression.raw,
                content_type=expression.mediatype,
            )
        except MetadataExpression.DoesNotExist:
            return HttpResponse(status=404)

    raise NotImplementedError


@sync_to_async
def get_expression(raw_hash):
    return MetadataExpression.objects.get(raw_hash=raw_hash)


async def expression_feed(request, mediatype):
    feed_expressions = await get_feed_expressions(mediatype)
    return JsonResponse({
        'expression-feed': [
            serialize_feed_expression(expression)
            for expression in feed_expressions
        ]
    }, status=200)


@sync_to_async
def get_feed_expressions(mediatype):
    # TODO-quest: pagination (cursor)
    # TODO-quest: consider allowing wildcard mediatypes like 'text/*', '*/*'
    return list(
        MetadataExpression.objects
        .filter(mediatype=mediatype)
        .defer('raw')
    )


def serialize_feed_expression(expression):
    url_to_raw_expression = reverse(
        'trove:raw-expression',
        kwargs={'raw-hash': expression.raw_hash},
    )
    return {
        'url-to-the-thing': expression.url_to_the_thing,
        'url-to-raw-expression': url_to_raw_expression,
        'raw-mediatype': expression.mediatype,
        'raw-hash': expression.raw_hash,
    }

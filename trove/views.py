
from asgiref.sync import sync_to_async
from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from trove.models.metadata_expression import MetadataExpression


# TODO-quest: json:api?


async def mediatype_basket(request):
    if request.method == 'GET':
        mediatypes = await get_all_mediatypes()
        return JsonResponse({'data': mediatypes})
    raise NotImplementedError


@sync_to_async
def get_all_mediatypes():
    return tuple(
        MetadataExpression.objects
        .values_list('mediatype', flat=True)
        .distinct('mediatype')
    )


async def expression_basket(request, url_to_the_thing):
    if request.method == 'GET':
        expression_basket = await get_expression_basket(url_to_the_thing)
        # TODO-quest: HTML page
        return HttpResponse(expression_basket)

    if request.method == 'PUT':
        await put_expression_in_basket(
            url_to_the_thing=url_to_the_thing,
            mediatype=request.headers['Content-Type'],
            raw_expression=request.body,
        )
        # TODO-quest: helpful response body
        return HttpResponse(status=201)

    raise NotImplementedError


@sync_to_async
def get_expression_basket(url_to_the_thing):
    expression_qs = (
        MetadataExpression.objects
        .filter(url_to_the_thing=url_to_the_thing)
        .values(
            'mediatype',
            'hashed_expression',
            # TODO-quest: url for expression_basket
        )
    )
    return '\n'.join(
        f"{v['mediatype']}: {v['hashed_expression']}"
        for v in expression_qs
    )


@sync_to_async
def put_expression_in_basket(url_to_the_thing, mediatype, raw_expression):
    # TODO-quest auth

    expression = MetadataExpression(
        url_to_the_thing=url_to_the_thing,
        mediatype=mediatype,
        raw_expression=raw_expression,
    )
    expression.compute_hash()
    expression.save()
    return HttpResponse(status=201)


async def raw_expression(request, hashed_expression):
    if request.method == 'GET':
        try:
            expression = await get_expression(hashed_expression)
            return HttpResponse(
                expression.raw_expression,
                content_type=expression.mediatype,
            )
        except MetadataExpression.DoesNotExist:
            return HttpResponse(status=404)

    raise NotImplementedError


@sync_to_async
def get_expression(hashed_expression):
    return MetadataExpression.objects.get(hashed_expression=hashed_expression)


async def expression_feed(request, mediatype):
    feed_expressions = await get_feed_expressions(mediatype)

    serialized_expressions = [
        {
            **expression_values,
            'url_to_raw_expression': reverse('trove:raw_expression', kwargs={
                'hashed_expression': expression_values['hashed_expression'],
            }),
        }
        for expression_values in feed_expressions
    ]
    return JsonResponse({
        'data': serialized_expressions,
    }, status=200)


@sync_to_async
def get_feed_expressions(mediatype):
    # TODO-quest: pagination (cursor)
    # TODO-quest: consider allowing wildcard mediatypes like 'text/*', '*/*'
    return tuple(
        MetadataExpression.objects
        .filter(mediatype=mediatype)
        .values(
            'url_to_the_thing',
            'mediatype',
            'hashed_expression',
        )
    )

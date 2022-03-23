from django.urls import path

from trove import views


app_name = 'trove'


urlpatterns = [
    path('mediatype-basket', views.mediatype_basket, name='mediatype-basket'),
    path('expression-basket///<path:url_to_the_thing>', views.expression_basket, name='expression-basket'),
    path('expression-feed///<path:raw_mediatype>', views.expression_feed, name='expression-feed'),
    path('raw-expression///<str:raw_hash>', views.raw_expression, name='raw-expression'),
]

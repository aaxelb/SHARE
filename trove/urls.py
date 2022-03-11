from django.urls import path

from trove import views


app_name = 'trove'


urlpatterns = [
    path('mediatype_basket', views.mediatype_basket, name='mediatype_basket'),
    path('expression_basket///<path:url_to_the_thing>', views.expression_basket, name='expression_basket'),
    path('expression_feed///<path:mediatype>', views.expression_feed, name='expression_feed'),
    path('raw_expression///<str:hashed_expression>', views.raw_expression, name='raw_expression'),
]

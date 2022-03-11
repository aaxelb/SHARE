from django.urls import path


from trove import views


urlpatterns = [
    path('expression_basket/<path:object_url>', views.expression_basket, name='expression_basket'),
    path('expression/<str:content_hash>', views.expression, name='expression'),
    path('feed/<path:content_type>', views.feed, name='feed'),
]

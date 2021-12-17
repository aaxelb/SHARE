from django.urls import path

from . import views


urlpatterns = [
    path('pls-format-metadata', views.pls_format_metadata),
]

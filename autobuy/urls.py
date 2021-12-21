from django.urls import path

from . import views


app_name = 'buy'
urlpatterns = [
    path('buy/', views.base_view, name='base')
]
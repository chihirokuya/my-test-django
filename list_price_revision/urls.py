from django.urls import path

from . import views


app_name = 'price'
urlpatterns = [
    path('price/', views.base_view, name='price-base'),
    path('price/asin/', views.asin_view, name='asin'),
    path('price/listing/', views.listing_view, name='listing'),
    path('price/blacklist/', views.blacklist_view, name='blacklist'),
    path('price/setting/', views.setting_view, name='setting'),
    path('price/log/', views.log_view, name='log'),
    path('price/listing/new/', views.get_table, name='get_listing'),
]
from django.urls import path

from . import views


app_name = 'price'
urlpatterns = [
    path('price/', views.base_view, name='price-base'),
    path('price/selling-stock', views.sell_and_not_stock, name='selling-stock'),
    path('price/asin/', views.asin_view, name='asin'),
    path('price/listing/', views.listing_view, name='listing'),
    path('price/blacklist/', views.blacklist_view, name='blacklist'),
    path('price/setting/', views.setting_view, name='setting'),
    path('price/log/', views.log_view, name='log'),
    path('price/log/get/', views.get_log, name='get_log'),
    path('price/listing/get/', views.get_table, name='get_listing'),
]
from django.urls import path

from . import views


app_name = 'price'
urlpatterns = [
    path('', views.base_view, name='price-base'),
    path('selling-stock', views.sell_and_not_stock, name='selling-stock'),
    path('asin/', views.asin_view, name='asin'),
    path('listing/', views.listing_view, name='listing'),
    path('blacklist/', views.blacklist_view, name='blacklist'),
    path('setting/', views.setting_view, name='setting'),
    path('log/', views.log_view, name='log'),
    path('log/get', views.get_log, name='get_log'),
    path('log/get/<int:range>', views.get_log, name='get_log'),
    path('listing/get/', views.get_table, name='get_listing'),

    path('api/asins', views.get_asin_data, name='api_asins')
]
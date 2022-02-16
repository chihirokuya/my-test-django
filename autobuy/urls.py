from django.urls import path

from . import views


app_name = 'buy'
urlpatterns = [
    path('order-list/', views.order_view, name='order'),
    path('order-list/<int:mode>', views.order_page_api, name='order'),
    path('buy/setting', views.setting_view, name='setting'),

    # order api list
    path('order/api/getAllOrders', views.get_orders),
    path('order/api/updateOrders', views.update_orders),  # success and fail
    path('order/api/deleteOrders', views.delete_orders),
]
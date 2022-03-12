from django.urls import path

from . import views


app_name = 'buy'
urlpatterns = [
    path('order-list/', views.order_view, name='order'),
    path('order-list/<int:mode>', views.order_page_api, name='order'),
    path('buy/setting', views.setting_view, name='setting'),
    path('buy/delivered-list', views.delivered_view, name='delivered'),
    path('buy/profit-table', views.profit_table_view, name='profit-table'),

    # order api list
    path('order/api/getAllOrders', views.get_orders),
    path('order/api/deleteOrders', views.cancel_order),
    path('order/api/myDeliveryInfo', views.get_my_delivery_info),
    path('order/api/editOrders', views.edit_orders),
    path('order/api/updateFailedNew', views.update_from_errors_to_new, name="failed_new"),
    path('order/api/getUserInfo', views.get_user_base_info),
    path('order/api/setSales', views.set_sales),
    path('order/api/getSales', views.get_sales, name='getSales'),
    path('order/api/getDateRange', views.get_date_range, name='getDateRange'),
    path('order/api/deleteSales', views.delete_all_sales, name='deleteSales'),
    path('order/api/sendOrder', views.send_order),
]
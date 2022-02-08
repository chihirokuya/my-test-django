from django.urls import path

from . import views


app_name = 'buy'
urlpatterns = [
    path('order-list/', views.order_view, name='order'),
    path('order-list/<int:mode>', views.order_page_api, name='order')
]
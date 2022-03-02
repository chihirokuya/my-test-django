from django.contrib import admin
from .models import OrderModel, BuyUserModel, DeliveredOrderModel, SalesModel

admin.site.register(OrderModel)
admin.site.register(BuyUserModel)
admin.site.register(DeliveredOrderModel)
admin.site.register(SalesModel)

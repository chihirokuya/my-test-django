from django.contrib import admin
from .models import OrderModel, BuyUserModel, DeliveredOrderModel, SalesModel, AsinSalesModel

admin.site.register(OrderModel)
admin.site.register(BuyUserModel)
admin.site.register(DeliveredOrderModel)
admin.site.register(SalesModel)
admin.site.register(AsinSalesModel)

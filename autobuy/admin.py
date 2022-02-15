from django.contrib import admin
from .models import OrderModel, BuyUserModel

admin.site.register(OrderModel)
admin.site.register(BuyUserModel)

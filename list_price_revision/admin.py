from django.contrib import admin

# Register your models here.
from .models import UserModel, AsinModel, RecordsModel, ListingModel


admin.site.register(UserModel)
admin.site.register(AsinModel)
admin.site.register(RecordsModel)
admin.site.register(ListingModel)

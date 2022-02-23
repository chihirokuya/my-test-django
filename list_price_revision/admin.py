from django.contrib import admin

# Register your models here.
from .models import UserModel, AsinModel, RecordsModel, ListingModel, Q10ItemsLink, Q10BrandCode, LogModel


class AsinAdmin(admin.ModelAdmin):
    search_fields = ['asin', 'brand']


class BrandAdmin(admin.ModelAdmin):
    search_fields = ['brand_name']


class ListingAdmin(admin.ModelAdmin):
    search_fields = ['username']


admin.site.register(UserModel)
admin.site.register(AsinModel, AsinAdmin)
admin.site.register(RecordsModel)
admin.site.register(ListingModel, ListingAdmin)
admin.site.register(Q10ItemsLink)
admin.site.register(Q10BrandCode,
                    BrandAdmin)
admin.site.register(LogModel)

from django.contrib import admin

# Register your models here.
from .models import UserModel, AsinModel, RecordsModel, ListingModel, Q10ItemsLink, Q10BrandCode


admin.site.register(UserModel)
admin.site.register(AsinModel)
admin.site.register(RecordsModel)
admin.site.register(ListingModel)
admin.site.register(Q10ItemsLink)
admin.site.register(Q10BrandCode)

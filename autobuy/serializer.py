from rest_framework import serializers
from .models import BuyUserModel, SingleSaleModel


class BuyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyUserModel
        fields = '__all__'


class SingleSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleSaleModel
        fields = ('order_num', 'order_date', 'product_name', 'qty', 'name', 'phone_num',
                  'mobile_num', 'address', 'post_code', 'q10_price', 'user_code', 'price',
                  'point', 'purchase_fee', 'amazon_order_num', 'profit', 'kotei', 'commission_fee', 'discount')
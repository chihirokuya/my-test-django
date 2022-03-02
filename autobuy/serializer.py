from rest_framework import serializers
from .models import BuyUserModel


class BuyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyUserModel
        fields = '__all__'
from rest_framework import serializers
from .models import AsinModel


class AsinSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsinModel
        fields = '__all__'
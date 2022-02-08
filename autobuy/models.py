from django.db import models


class OrderModel(models.Model):
    username = models.CharField(max_length=1000, blank=True)

    order_list = models.JSONField(blank=True)

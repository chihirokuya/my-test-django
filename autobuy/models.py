from django.db import models


class OrderModel(models.Model):
    username = models.TextField(blank=True)

    order_list = models.JSONField(blank=True)


class BuyUserModel(models.Model):
    username = models.TextField(blank=True, null=True)

    # Amazonアカウント
    mail_address = models.TextField(default='', blank=True, null=True)
    mail_pass = models.TextField(default='', blank=True, null=True)
    credit_card = models.TextField(default='', blank=True, null=True)

    # 請求先住所
    name = models.TextField(default='', blank=True, null=True)
    post_num = models.TextField(default='', blank=True, null=True)
    prefecture = models.TextField(default='', blank=True, null=True)
    address = models.TextField(default='', blank=True, null=True)
    phone_num = models.TextField(default='', blank=True, null=True)

    # その他
    mega_wari = models.BooleanField(default=False, null=True, blank=True)
    akaji = models.IntegerField(default=0, blank=True, null=True)
    card_res = models.IntegerField(default=0, blank=True, null=True)
    commission_fee = models.IntegerField(default=0, blank=True, null=True)
    proxy = models.JSONField(blank=True, null=True)
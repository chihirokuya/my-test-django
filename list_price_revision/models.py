from django.db import models
import datetime

delimiter = "delimiter"


class UserModel(models.Model):
    username = models.CharField(max_length=1000, blank=True)

    # q10アカウント
    q10_id = models.CharField(max_length=1000, blank=True)
    q10_password = models.CharField(max_length=1000, blank=True)
    q10_api = models.CharField(max_length=1000, blank=True, default='')

    # Q10出品情報
    description_header = models.TextField(default='', null=True, blank=True)
    description_footer = models.TextField(default='', blank=True)
    initial_letter = models.CharField(max_length=1, blank=True)
    delete_or_not = models.BooleanField(default=False, blank=True)
    shipping_code = models.CharField(max_length=1000, default='', blank=True)
    stock_num = models.IntegerField(default=3, blank=True)
    photo_num = models.IntegerField(default=3, blank=True)

    # ブラックリスト
    maker_name_blacklist = models.TextField(default='', blank=True)
    asin_blacklist = models.TextField(default='', blank=True)
    words_blacklist = models.TextField(default='', blank=True)
    group_black = models.TextField(default='', blank=True)

    # 価格関連
    max_1 = models.IntegerField(default=0, blank=True)
    max_2 = models.IntegerField(default=0, blank=True)
    max_3 = models.IntegerField(default=0, blank=True)
    rieki_1 = models.IntegerField(default=0, blank=True)
    rieki_2 = models.IntegerField(default=0, blank=True)
    rieki_3 = models.IntegerField(default=0, blank=True)
    rieki_4 = models.IntegerField(default=0, blank=True)
    kotei_1 = models.IntegerField(default=0, blank=True)
    kotei_2 = models.IntegerField(default=0, blank=True)
    kotei_3 = models.IntegerField(default=0, blank=True)
    kotei_4 = models.IntegerField(default=0, blank=True)


class ListingModel(models.Model):
    username = models.CharField(max_length=1000, blank=True)

    # 出品中ASIN
    asin_list = models.TextField(default='', blank=True)

    # 出品待ち
    asin_waiting_list = models.TextField(default='', blank=True, null=True)

    # 取得中
    asin_getting_list = models.TextField(default='', blank=True, null=True)


class AsinModel(models.Model):
    asin = models.CharField(max_length=10)

    product_name = models.TextField(blank=True, default='')
    brand = models.TextField(blank=True, default='')
    product_group = models.TextField(blank=True, default='')
    photo_list = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    jan = models.TextField(max_length=100, default='', blank=True)
    category_tree = models.JSONField(blank=True, default={})
    price = models.IntegerField(default=0, blank=True)

    q10_category = models.CharField(default='', blank=True, max_length=10000)


class RecordsModel(models.Model):
    username = models.CharField(max_length=1000, null=True, default='')
    date = models.DateTimeField(default=datetime.datetime.now(), null=True, blank=True)

    total_length = models.IntegerField(null=True, default=0, blank=True)
    new_length = models.IntegerField(null=True, default=0, blank=True)

    already_listed = models.BooleanField(null=True, blank=True, default=False)

    asin_list = models.TextField(null=True, default='', blank=True)


class Q10BrandCode(models.Model):
    brand_name = models.CharField(max_length=10000)
    code = models.CharField(max_length=10000)


class Q10ItemsLink(models.Model):
    username = models.CharField(max_length=1000)

    total_asin_list = models.TextField(default='', null=True, blank=True)
    linked_asin_list = models.TextField(default='', null=True, blank=True)

    still_getting = models.BooleanField(default=False, null=True, blank=True)


class LogModel(models.Model):
    username = models.CharField(max_length=1000)

    date = models.DateTimeField()
    # 価格改定or出品or削除
    type = models.CharField(max_length=1000)
    # 動作を行う際に入ってくるasinリスト
    input_asin_list = models.TextField(default='', null=True, blank=True)
    # 成功したリスト
    success_asin_list = models.TextField(default='', null=True, blank=True)
    # 失敗理由リスト　区切り単語："delimiter"
    cause_list = models.TextField(default='', null=True, blank=True)
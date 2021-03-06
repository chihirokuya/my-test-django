from django.db import models
import datetime

delimiter = "delimiter"


class UserModel(models.Model):
    username = models.TextField(blank=True)

    # q10アカウント
    q10_id = models.TextField(blank=True)
    q10_password = models.TextField(blank=True)
    q10_api = models.TextField(blank=True, default='')

    # Q10出品情報
    description_header = models.TextField(default='', null=True, blank=True)
    description_footer = models.TextField(default='', blank=True)
    initial_letter = models.TextField(max_length=1, blank=True)
    delete_or_not = models.BooleanField(default=False, blank=True)
    shipping_code = models.TextField(default='', blank=True)
    stock_num = models.IntegerField(default=3, blank=True)
    photo_num = models.IntegerField(default=3, blank=True)

    # ブラックリスト
    maker_name_blacklist = models.TextField(default='', blank=True)
    asin_blacklist = models.TextField(default='', blank=True)
    words_blacklist = models.TextField(default='', blank=True)
    group_black = models.TextField(default='', blank=True)

    # 価格関連
    min_1 = models.IntegerField(default=0, null=True, blank=True)
    max_1 = models.IntegerField(default=0, blank=True)
    max_2 = models.IntegerField(default=0, blank=True)
    max_3 = models.IntegerField(default=0, blank=True)
    max_4 = models.IntegerField(default=0, blank=True)
    rieki_1 = models.IntegerField(default=0, blank=True)
    rieki_2 = models.IntegerField(default=0, blank=True)
    rieki_3 = models.IntegerField(default=0, blank=True)
    rieki_4 = models.IntegerField(default=0, blank=True)
    kotei_1 = models.IntegerField(default=0, blank=True)
    kotei_2 = models.IntegerField(default=0, blank=True)
    kotei_3 = models.IntegerField(default=0, blank=True)
    kotei_4 = models.IntegerField(default=0, blank=True)

    # API確認終わっているか。
    api_ok = models.BooleanField(default=False, null=True, blank=True)

    shop_name = models.TextField(default='', blank=True, null=True)


class ListingModel(models.Model):
    username = models.TextField(blank=True)

    # 出品中ASIN
    asin_list = models.TextField(default='', blank=True)

    # 出品待ち
    asin_waiting_list = models.TextField(default='', blank=True, null=True)

    # 取得中: 同じASINが２回入ってきた時に、片方のみを処理する用。
    asin_getting_list = models.TextField(default='', blank=True, null=True)

    # 販売中
    selling_list = models.TextField(default='')

    # 在庫切れ
    no_stock_list = models.TextField(default='')


class AsinModel(models.Model):
    asin = models.TextField()

    product_name = models.TextField(blank=True, default='')
    brand = models.TextField(blank=True, default='')
    product_group = models.TextField(blank=True, default='')
    photo_list = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    jan = models.TextField(max_length=100, default='', blank=True)
    category_tree = models.JSONField(blank=True, default={})
    price = models.IntegerField(default=0, blank=True)
    point = models.IntegerField(default=0, blank=True, null=True)

    q10_category = models.TextField(default='', blank=True)

    def ph(self):
        return self.photo_list.split('\n')[0]

    def brand_name(self):
        try:
            brand_obj: Q10BrandCode = Q10BrandCode.objects.get(code=self.brand)
            return brand_obj.brand_name
        except:
            return ''

    sell_num = models.IntegerField(default=0, blank=True, null=True)

    in_black_list = models.BooleanField(default=False, blank=True, null=True)

    # 選択制ある場合 [{price, point, name}]
    variation_options = models.JSONField(default=[])
    # 選択制がある場合の最初の名称
    base_name = models.TextField(default='')
    base_asin = models.TextField(default='')


class RecordsModel(models.Model):
    username = models.TextField(null=True, default='')
    date = models.DateTimeField(default=datetime.datetime.now(), null=True, blank=True)

    total_length = models.IntegerField(null=True, default=0, blank=True)
    new_length = models.IntegerField(null=True, default=0, blank=True)

    already_listed = models.BooleanField(null=True, blank=True, default=False)

    asin_list = models.TextField(null=True, default='', blank=True)

    status_text = models.TextField(null=True, default='', blank=True)


class Q10BrandCode(models.Model):
    brand_name = models.TextField()
    code = models.TextField()


class Q10ItemsLink(models.Model):
    username = models.TextField()

    total_asin_list = models.TextField(default='', null=True, blank=True)
    linked_asin_list = models.TextField(default='', null=True, blank=True)

    still_getting = models.BooleanField(default=False, null=True, blank=True)


class LogModel(models.Model):
    username = models.TextField()

    date = models.DateTimeField()
    # 価格改定or出品or削除
    type = models.TextField()
    # 動作を行う際に入ってくるasinリスト
    input_asin_list = models.TextField(default='', null=True, blank=True)
    # 成功したリスト
    success_asin_list = models.TextField(default='', null=True, blank=True)
    # 失敗理由リスト　区切り単語："delimiter"
    cause_list = models.TextField(default='', null=True, blank=True)

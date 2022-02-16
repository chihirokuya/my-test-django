from django.db import models


cancel_message = "ご注文ありがとうございます。\n"\
                "\n" \
                "ご注文された商品ですが、新型コロナウイルスの影響でメーカーから出荷ができないとの急遽連絡がありました。\n" \
                 "\n" \
                 "大変申し訳ございませんが、キャンセル処理をさせていただきます。\n" \
                 "\n" \
                 "当ショップから返金できないシステムのためお客様からQoo10カスタマーへいずれかの方法でお問い合わせをお願いいたします。\n" \
                 "\n" \
                 "また商品代金の返金はQoo10から行われます。返金方法は2種類ございますのでどちらかを選択いただければと存じます。\n" \
                 "\n" \
                 "〇返金について\n" \
                 "(1)Qサイフへの返金\n" \
                 "Qサイフとは、Qoo10でお買いものできるサイバーマネーです。Qサイフ内の精算金は、Qoo10で現金と同じように商品を購入する際にご使用いただけます。\n" \
                 "\n" \
                 "(2) お客様の指定口座への返金（手数料無料）\n" \
                 "電話お問い合わせ：(050-5840-9100)\n" \
                 "受付時間 09:00~18:00(土日・祝日を除く)\n" \
                 "Mail：help@qoo10.jp\n" \
                 "購入者様専用カスタマーセンターメールフォーマット\n" \
                 "https://www.qoo10.jp/gmkt.inc/CS/NHelpContactUs.aspx\n" \
                 "以上、よろしくお願いいたします。\n" \
                 "またのご注文を心よりお待ちしております。"


class OrderModel(models.Model):
    username = models.TextField(blank=True)

    order_list = models.JSONField(default=[], blank=True)

    failed_order_list = models.JSONField(default=[], blank=True)


class BuyUserModel(models.Model):
    username = models.TextField(blank=True)

    # Amazonアカウント
    mail_address = models.TextField(default='', blank=True)
    mail_pass = models.TextField(default='', blank=True)
    credit_card = models.TextField(default='', blank=True)

    # 請求先住所
    name = models.TextField(default='', blank=True)
    post_num = models.TextField(default='', blank=True)
    prefecture = models.TextField(default='', blank=True)
    address = models.TextField(default='', blank=True)
    phone_num = models.TextField(default='', blank=True)
    cancel_message = models.TextField(default=cancel_message, blank=True)

    # その他
    mega_wari = models.BooleanField(default=False, blank=True)
    akaji = models.IntegerField(default=0, blank=True)
    card_res = models.IntegerField(default=0, blank=True)
    commission_fee = models.IntegerField(default=0, blank=True)
    proxy = models.JSONField(default=[], blank=True)
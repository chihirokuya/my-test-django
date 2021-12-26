from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
import datetime
from list_price_revision.models import ListingModel, RecordsModel, AsinModel
import threading
from list_price_revision.api import get_info_from_amazon, upload_new_item, get_certification_key, link_q10_items, SpApiFunction


@shared_task
def records_saved(username, date):
    """
    obj.asin_list: 出品済みリスト
    obj.asin_waiting_list: ASINを取得中または出品待ち
    obj.asin_getting_list: すでにASINを取得中（出品は関係ない）。これに入っているASINはto_search_listから外す。

    1: usernameに対応するListingModel、RecordsModelを取得してくる。
    2: waiting_listにあるASIN情報を取得し、AsinModelに追加する。その際にAsinModelまたはasin_getting_listにあるものは省く。
    3: asin_getting_listを更新する。

    どのASINがまだ価格＆情報取得していないかを確認。その後それらを取得。(to_search_list) OK
    同時に商品が存在しないなどの理由でwaiting_listから消したいASINを別に保存。(to_delete_list) OK
    削除するASINを削除する。 OK

    AsinModelに追加。 OK

    出品を行う。
    OKなものからasin_waiting_listから消し、asin_listに移動。 OK
    obj.save() OK

    最後にRecordModelを更新し完了。
    """

    obj = ListingModel.objects.get(username=username)
    corresponding_record_object = RecordsModel.objects.get(username=username, date=date)
    certification_key = get_certification_key(username)

    asin_waiting_list: list = list(obj.asin_waiting_list.split(','))
    asin_list = list(obj.asin_list.split(','))
    asin_getting_list = list(obj.asin_getting_list.split(','))

    new_getting_list = []
    to_transfer_list = []
    to_list_but_still_in_waiting = []

    to_search_list = []
    for asin in asin_waiting_list:
        if not AsinModel.objects.filter(asin=asin).exists() and asin not in asin_getting_list:
            asin_getting_list.append(asin)
            new_getting_list.append(asin)
            to_search_list.append(asin)
        else:
            if asin in asin_list:
                asin_waiting_list.remove(asin)
            to_list_but_still_in_waiting.append(asin)

    obj.asin_getting_list = ','.join(asin_getting_list)
    obj.save()

    print('search list', to_search_list)
    if to_search_list:
        # 個数を確認し、5個またはそれ以下のThreadを作成
        class ToSearchThread:
            result_list = {}
            to_delete_asin_list = []

            def __init__(self):
                self.result_list = {}
                self.to_delete_asin_list = []

        if len(to_search_list) > 10:
            thread_num = 5
        else:
            thread_num = 1

        length = len(to_search_list) // thread_num
        divided_list = [to_search_list[i * length: (i + 1) * length] for i in range(thread_num - 1)]
        divided_list.append(to_search_list[(thread_num - 1) * length:])

        threads = []
        to_search_class = ToSearchThread
        for i in range(thread_num):
            threads.append(threading.Thread(
                target=get_info_from_amazon,
                kwargs={
                    "to_search_class": to_search_class,
                    'asin_list': divided_list[i],
                    "certification_key": certification_key
                }
            ))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        print('削除開始')
        print(to_search_class.to_delete_asin_list)
        # DeleteListを参考にasin_waiting_listから削除していく
        for asin in to_search_class.to_delete_asin_list:
            try:
                asin_waiting_list.remove(asin)
            except:
                pass
        print('削除完了')

        print('ASINモデル追加開始')
        # ASINモデルを追加していく
        for key in to_search_class.result_list.keys():
            if not AsinModel.objects.filter(asin=key).exists():
                try:
                    temp = to_search_class.result_list[key]
                    AsinModel(
                        asin=key,
                        product_name=temp['name'],
                        brand=temp['brand'],
                        product_group=temp['group'],
                        photo_list='\n'.join(temp['links']),
                        description='\n'.join(temp['description']),
                        jan=temp['jan'],
                        category_tree=temp['category_tree'],
                        price=int(temp['price']),
                        q10_category=temp['q10_category']
                    ).save()
                    to_transfer_list.append(key)
                except:
                    print('追加失敗ASIN：', key)
            else:
                to_transfer_list.append(key)
        print('追加完了')
    else:
        print('search_listが空なためasin_listに直で追加します。')

    to_transfer_list.extend(to_list_but_still_in_waiting)

    # 出品→asin_waitingからasin_listに移す
    print(to_transfer_list)
    for asin in to_transfer_list:
        if upload_new_item(asin, username, certification_key):
            print('OK')
            try:
                asin_waiting_list.remove(asin)
            except:
                pass

            try:
                asin_getting_list.remove(asin)
            except:
                pass

            asin_list.append(asin)
        else:
            print('waiting', asin_waiting_list)


    obj.asin_list = ','.join(list(filter(None, asin_list)))
    obj.asin_waiting_list = ','.join(list(filter(None, asin_waiting_list)))
    obj.asin_getting_list = ','.join([val for val in obj.asin_getting_list.split(',') if val not in new_getting_list])
    obj.save()

    corresponding_record_object.already_listed = True
    corresponding_record_object.save()

    print('完了')


@shared_task
def link_q10_account(username):
    """
    ListingModel上でusernameに対応するasin_listに追加していく。
    """
    certification_key = get_certification_key(username)

    link_q10_items(certification_key, username)


@shared_task
def re_price():
    print(datetime.datetime.today(), '価格改定開始')

    objects = AsinModel.objects.all()
    total_length = len(objects)

    def update_prices(thread_objects):
        print('start update')

        sp_api = SpApiFunction()

        for obj in thread_objects:
            offers = sp_api.get_offers(obj.asin)

            if offers is None:
                continue

            if offers.errors is not None:
                continue

            price = sp_api.get_lowest_price(offers)

            print(price)

            if price:
                obj.asin = int(price)
                obj.save()

    thread_num = 5

    length = len(objects) // thread_num
    divided_list = [objects[i * length: (i + 1) * length] for i in range(thread_num - 1)]
    divided_list.append(objects[(thread_num - 1) * length:])

    print(divided_list)

    threads = []
    for i in range(thread_num):
        threads.append(threading.Thread(
            target=update_prices,
            kwargs={
                'thread_objects': divided_list[i],
            }
        ))

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
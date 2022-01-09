from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
import datetime
from list_price_revision.models import ListingModel, RecordsModel, AsinModel, UserModel, LogModel
import threading
from list_price_revision.api import get_info_from_amazon, upload_new_item, get_certification_key, link_q10_items, SpApiFunction, delete_item, update_price
from list_price_revision.views import delimiter
from django.contrib.auth import get_user_model


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

    # ログ用
    log_success_asin_list = []
    log_failed_asin_list = []

    to_search_list = []
    for asin in asin_waiting_list:
        if not AsinModel.objects.filter(asin=asin).exists() and asin not in asin_getting_list:
            asin_getting_list.append(asin)
            new_getting_list.append(asin)
            to_search_list.append(asin)
        else:
            if asin in asin_list:
                asin_waiting_list.remove(asin)
                continue
            to_list_but_still_in_waiting.append(asin)

    obj.asin_getting_list = ','.join(asin_getting_list)
    obj.save()

    print('search list', to_search_list)
    if to_search_list:
        # 個数を確認し、5個またはそれ以下のThreadを作成
        class ToSearchThread:
            result_list = {}
            to_delete_asin_list = []
            log_error_reason = []

            def __init__(self):
                self.result_list = {}
                self.to_delete_asin_list = []
                self.log_error_reason = []

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
                    "username": username,
                    "to_search_class": to_search_class,
                    'asin_list': divided_list[i],
                    "certification_key": certification_key
                }
            ))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # ログに削除理由追加
        for val in to_search_class.log_error_reason:
            try:
                log_failed_asin_list.append(val)
            except:
                pass

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
                except Exception as e:
                    log_failed_asin_list.append([key, str(e)])
                    print('追加失敗ASIN：', key)
            else:
                log_failed_asin_list.append(key)
                to_transfer_list.append(key)
        print('追加完了')
    else:
        print('search_listが空なためasin_listに直で追加します。')

    to_transfer_list.extend(to_list_but_still_in_waiting)

    to_transfer_list = list(filter(None, to_transfer_list))

    # 出品→asin_waitingからasin_listに移す
    print(to_transfer_list)
    for asin in to_transfer_list:
        ok, reason = upload_new_item(asin, username, certification_key)
        if ok:
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
            log_success_asin_list.append(asin)
        else:
            log_failed_asin_list.append([asin, reason])

            if reason == '出品失敗':
                try:
                    asin_waiting_list.remove(asin)
                except:
                    pass

    obj.asin_list = ','.join(list(filter(None, asin_list)))
    obj.asin_waiting_list = ','.join(list(filter(None, asin_waiting_list)))
    obj.asin_getting_list = ','.join([val for val in obj.asin_getting_list.split(',') if val not in new_getting_list])
    obj.save()

    corresponding_record_object.already_listed = True
    corresponding_record_object.save()

    # 失敗理由リスト　区切り単語："delimiter"
    temp = [val[0] for val in log_failed_asin_list]
    log_total_list = temp
    log_total_list.extend(log_success_asin_list)
    cause_list = ''
    for val in log_failed_asin_list:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    LogModel(username=username, type='出品', input_asin_list=','.join(log_total_list),
             success_asin_list=','.join(log_success_asin_list), cause_list=cause_list,
             date=datetime.datetime.now()).save()

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

    # ログ用
    total = []
    success = []
    failed = []

    def add_log(ok, asin, reason=''):
        total.append(asin)
        if ok:
            success.append(asin)
        else:
            failed.append([asin, reason])

    def update_prices(thread_objects):
        print('start update')

        sp_api = SpApiFunction()

        print(thread_objects)

        for obj in thread_objects:
            offers = sp_api.get_offers('B' + obj.asin[1:])

            if offers is None:
                add_log(False, obj.asin, '存在しないASIN')
                continue

            if offers.errors is not None:
                add_log(False, obj.asin, '存在しないASIN')
                continue

            price = sp_api.get_lowest_price(offers.payload)

            print(f'price {price}')

            if price:
                add_log(True, obj.asin)
                obj.price = int(price)
            else:
                obj.price = 0
                add_log(False, obj.asin, '価格取得失敗')

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

    cause_list = ''
    for val in failed:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    LogModel(username='admin', type='価格改定', input_asin_list=','.join(total),
             success_asin_list=','.join(success), cause_list=cause_list,
             date=datetime.datetime.now()).save()


@shared_task
def delete_items(username, to_delete_asin_list):
    obj: ListingModel = ListingModel.objects.get(username=username)
    certification_key = get_certification_key(username)

    user_obj = UserModel.objects.get(username=username)
    initial_letter = user_obj.initial_letter

    log_success_list = []
    log_failed_list = []

    for asin in to_delete_asin_list:
        # If deleted remove also from obj.asin_list
        res = delete_item(certification_key, initial_letter + asin[1:])
        if type(res) == bool and res:
            asin_list = obj.asin_list.split(',')
            asin_list.remove(asin) if asin in asin_list else asin_list
            obj.asin_list = ','.join(asin_list)
            obj.save()
            log_success_list.append(asin)
        else:
            log_failed_list.append([asin, res[1]])

    cause_list = ''
    for val in log_failed_list:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    LogModel(username=username, date=datetime.datetime.now(),
             type='削除', input_asin_list=','.join(to_delete_asin_list),
             success_asin_list=','.join(log_success_list), cause_list=cause_list).save()


@shared_task
def re_price_users():
    users = list(dict.fromkeys([str(val) for val in get_user_model().objects.all()]))

    for user in users:
        threading.Thread(
            target=update_price,
            kwargs={
                "username": user
            }
        ).start()
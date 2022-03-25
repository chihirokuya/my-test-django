from __future__ import absolute_import, unicode_literals
from celery import shared_task
import datetime
from list_price_revision.models import ListingModel, RecordsModel, AsinModel, UserModel, LogModel
import threading
from list_price_revision.api import get_info_from_amazon, upload_new_item, get_certification_key, link_q10_items, SpApiFunction, delete_item, update_price,\
                                                    get_info_and_add_to_database
from list_price_revision.models import delimiter
from django.contrib.auth import get_user_model
import pytz


class CounterClass:
    log_error_reason = []
    was_variation = [] # [base_asin, new_asin]
    total_length = 0
    counter = 0
    step_2_counter = 0

    def __init__(self, total_length):
        self.log_error_reason = []
        self.total_length = total_length
        self.was_variation = [] # [base_asin, new_asin]

        self._lock = threading.Lock()

    def increment(self, l):
        with self._lock:
            self.step_2_counter += l

    def increment_1(self, l):
        with self._lock:
            self.counter += l


@shared_task
def new_shuppin(username, date):
    """
    obj: ListingModel
    obj.asin_list: 出品中リスト
    obj.asin_waiting_list: ASINを取得中または出品中
    obj.getting_list: ASIN取得中

    obj.selling_list:　販売中
    obj.no_stock_list: 在庫なし
    """
    obj = ListingModel.objects.get(username=username)
    corresponding_record_object = RecordsModel.objects.get(username=username, date=date)
    certification_key = get_certification_key(username)

    ################### clean up data ######################
    temp = obj.asin_list.split(',')
    waiting_list = [asin for asin in obj.asin_waiting_list.split(',') if asin and asin not in temp]
    obj.asin_waiting_list = ','.join(waiting_list)
    obj.save()

    log_failed_list = []
    log_success_list = []
    done_asin_list = [] #エラーが出た、またはデータベースに登録されたもの
    ########################################################

    #################### ASINから情報取得 #####################
    add_to_database_asin_list = []
    for asin in obj.asin_waiting_list.split(','):
        if not AsinModel.objects.filter(asin=asin).exists() and \
                not AsinModel.objects.filter(base_asin=asin).exists() and \
                    asin not in obj.asin_getting_list:
            add_to_database_asin_list.append(asin)

    current = obj.asin_getting_list.split(',')
    current.extend(add_to_database_asin_list)
    obj.asin_getting_list = ','.join(list(dict.fromkeys(current)))
    obj.save()

    if add_to_database_asin_list:
        thread_num = 5 if len(add_to_database_asin_list) > 10 else 1
        length = len(add_to_database_asin_list) // thread_num
        divided_list = [add_to_database_asin_list[i * length: (i + 1) * length] for i in range(thread_num - 1)]
        divided_list.append(add_to_database_asin_list[(thread_num - 1) * length:])

        threads = []
        counter_class = CounterClass(len(add_to_database_asin_list))
        for i in range(thread_num):
            threads.append(threading.Thread(
                target=get_info_and_add_to_database,
                kwargs={
                    "counter_class": counter_class,
                    'asin_list': divided_list[i],
                    "certification_key": certification_key,
                    "records_model": corresponding_record_object
                }
            ))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # ログに削除理由追加
        for val in counter_class.log_error_reason:
            try:
                done_asin_list.append(val[0])
                log_failed_list.append(val)
            except:
                pass
        waiting_list = obj.asin_waiting_list.split(',')
        for asin in done_asin_list:
            waiting_list.remove(asin) if asin in waiting_list else ''
        obj.asin_waiting_list = ','.join(waiting_list)

        getting_list = obj.asin_getting_list.split(',')
        for asin in add_to_database_asin_list:
            if asin in getting_list and (AsinModel.objects.filter(asin=asin).exists() or AsinModel.objects.filter(base_asin=asin).exists()):
                getting_list.remove(asin)
                done_asin_list.append(asin)
        obj.asin_getting_list = ','.join(getting_list)
        obj.save()
    else:
        print('データベースに追加する新たなASINはありませんでした。')
    #########################################################

    print(waiting_list, len(waiting_list))

    # エラー内容にもデータベース登録も行われなかったASINはエラーとして追加する
    waiting_list = obj.asin_waiting_list.split(',')
    getting_list = obj.asin_getting_list.split(',')
    asin_list = obj.asin_list.split(',')
    selling_list = obj.selling_list.split(',')

    for asin in waiting_list:
        if AsinModel.objects.filter(asin=asin).exists() or AsinModel.objects.filter(base_asin=asin).exists():
            done_asin_list.append(asin)

    print(len(done_asin_list))

    to_remove_from_waiting_list = []
    for asin in waiting_list:
        if asin not in done_asin_list:
            print('koko')
            log_failed_list.append([asin, 'エラー原因不明'])
            to_remove_from_waiting_list.append(asin)
    waiting_list = [asin for asin in waiting_list if asin not in to_remove_from_waiting_list]

    print(waiting_list, len(waiting_list))

    ######################## 出品 ###########################
    to_remove_from_waiting_list = []
    for asin in waiting_list:
        if AsinModel.objects.filter(asin=asin).exists():
            actual_asin = asin
        elif AsinModel.objects.filter(base_asin=asin).exists():
            actual_asin = AsinModel.objects.filter(base_asin=asin)[0].asin
        else:
            print(f'koko {asin}')
            log_failed_list.append([asin, 'エラー原因不明'])
            to_remove_from_waiting_list.append(asin)
            continue

        ok, reason = upload_new_item(actual_asin, username, certification_key)

        if ok:
            to_remove_from_waiting_list.append(asin)

            asin_list.append(actual_asin)
            selling_list.append(actual_asin)
            log_success_list.append(asin)
        else:
            print(f'failed {asin}')
            log_failed_list.append([asin, reason])

            if reason != '出品失敗':
                to_remove_from_waiting_list.append(asin)
    waiting_list = [asin for asin in waiting_list if asin not in to_remove_from_waiting_list]
    print(len(waiting_list))
    ########################################################

    obj.asin_list = ','.join(list(filter(None, asin_list)))
    obj.selling_list = ','.join(list(filter(None, selling_list)))
    obj.asin_waiting_list = ','.join(list(filter(None, waiting_list)))
    obj.asin_getting_list = ''
    obj.save()

    corresponding_record_object.already_listed = True
    corresponding_record_object.status_text = ''
    corresponding_record_object.save()

    # 失敗理由リスト　区切り単語："delimiter"
    temp = [val[0] for val in log_failed_list]
    log_total_list = temp
    log_total_list.extend(log_success_list)
    cause_list = ''
    for val in log_failed_list:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    LogModel(username=username, type='出品', input_asin_list=','.join(log_total_list),
             success_asin_list=','.join(log_success_list), cause_list=cause_list,
             date=datetime.datetime.now()).save()


# 出品
# @shared_task
# def records_saved(username, date):
#     """
#     obj.asin_list: 出品済みリスト
#     obj.asin_waiting_list: ASINを取得中または出品待ち
#     obj.asin_getting_list: すでにASINを取得中（出品は関係ない）。これに入っているASINはto_search_listから外す。
#
#     1: usernameに対応するListingModel、RecordsModelを取得してくる。
#     2: waiting_listにあるASIN情報を取得し、AsinModelに追加する。その際にAsinModelまたはasin_getting_listにあるものは省く。
#     3: asin_getting_listを更新する。
#
#     どのASINがまだ価格＆情報取得していないかを確認。その後それらを取得。(to_search_list) OK
#     同時に商品が存在しないなどの理由でwaiting_listから消したいASINを別に保存。(to_delete_list) OK
#     削除するASINを削除する。 OK
#
#     AsinModelに追加。 OK
#
#     出品を行う。
#     OKなものからasin_waiting_listから消し、asin_listに移動。 OK
#     obj.save() OK
#
#     最後にRecordModelを更新し完了。
#     """
#
#     obj = ListingModel.objects.get(username=username)
#     corresponding_record_object = RecordsModel.objects.get(username=username, date=date)
#     certification_key = get_certification_key(username)
#
#     asin_waiting_list: list = list(obj.asin_waiting_list.split(','))    # ASIN取得or出品待ち
#     asin_list = list(obj.asin_list.split(','))  # 出品中
#     selling_list = obj.selling_list.split(',')
#     asin_getting_list = list(obj.asin_getting_list.split(','))  # すでにASINを取得中動作に入っているもの
#
#     new_getting_list = []   # 新規取得ASINリスト
#     to_transfer_list = []   # Q10に出品するリスト
#     to_list_but_still_in_waiting = []   # すでにASIN情報取得は完了しているが、Q10への出品が完了していないリスト
#
#     # ログ用
#     log_success_asin_list = []
#     log_failed_asin_list = []
#
#     # 選択制が会った時の元ASINとあたらしいASIN
#     variation_asins = {}
#
#     to_search_list = []  # ASIN情報取得の必要があるリスト
#
#     for asin in asin_waiting_list:
#         # ASINがDB上に存在しない and ASIN_GETTING_LIST内に含まれていない ならSP-API&Keepaから取得
#         if not AsinModel.objects.filter(asin=asin).exists() and not AsinModel.objects.filter(base_asin=asin).exists() and asin not in asin_getting_list:
#             asin_getting_list.append(asin)  # ASIN_GETTING_LISTに追加
#             new_getting_list.append(asin)
#             to_search_list.append(asin)
#         else:
#             if asin in asin_list:
#                 asin_waiting_list.remove(asin)
#                 continue
#             if AsinModel.objects.filter(base_asin=asin).exists():
#                 to_transfer_list.append(AsinModel.objects.filter(base_asin=asin)[0].asin)
#                 asin_waiting_list.remove(asin)
#             to_list_but_still_in_waiting.append(asin)
#
#     obj.asin_getting_list = ','.join(asin_getting_list)
#     obj.save()
#
#     if to_search_list:
#         # 個数を確認し、5個またはそれ以下のThreadを作成
#         class ToSearchThread:
#             result_list = {}
#             to_delete_asin_list = []
#             log_error_reason = []
#             total_length = 0
#             counter = 0
#             step_2_counter = 0
#
#             def __init__(self, total_length):
#                 self.result_list = {}
#                 self.to_delete_asin_list = []
#                 self.log_error_reason = []
#                 self.total_length = total_length
#
#                 self._lock = threading.Lock()
#
#             def increment(self, l):
#                 with self._lock:
#                     self.step_2_counter += l
#
#         if len(to_search_list) > 10:
#             thread_num = 5
#         else:
#             thread_num = 1
#
#         length = len(to_search_list) // thread_num
#         divided_list = [to_search_list[i * length: (i + 1) * length] for i in range(thread_num - 1)]
#         divided_list.append(to_search_list[(thread_num - 1) * length:])
#
#         threads = []
#         to_search_class = ToSearchThread(len(to_search_list))
#         for i in range(thread_num):
#             threads.append(threading.Thread(
#                 target=get_info_from_amazon,
#                 kwargs={
#                     "username": username,
#                     "to_search_class": to_search_class,
#                     'asin_list': divided_list[i],
#                     "certification_key": certification_key,
#                     "records_model": corresponding_record_object
#                 }
#             ))
#
#         for thread in threads:
#             thread.start()
#         for thread in threads:
#             thread.join()
#
#         # ログに削除理由追加
#         for val in to_search_class.log_error_reason:
#             try:
#                 log_failed_asin_list.append(val)
#             except:
#                 pass
#
#         print('削除開始')
#         # DeleteListを参考にasin_waiting_listから削除していく
#         for asin in to_search_class.to_delete_asin_list:
#             try:
#                 asin_waiting_list.remove(asin)
#             except:
#                 pass
#         print('削除完了')
#
#         print('ASINモデル追加開始')
#         # ASINモデルを追加していく
#         for key in to_search_class.result_list.keys():
#             if not AsinModel.objects.filter(asin=key).exists():
#                 temp = to_search_class.result_list[key]
#                 print('rel', temp['relationships'])
#                 if temp['relationships']:
#                     variation_asins[key] = temp['original_asin']
#                     print(variation_asins)
#
#                 try:
#                     AsinModel(
#                         asin=key,
#                         product_name=temp['name'],
#                         brand=temp['brand'],
#                         product_group=temp['group'],
#                         photo_list='\n'.join(temp['links']),
#                         description='\n'.join(temp['description']),
#                         jan=temp['jan'],
#                         category_tree=temp['category_tree'],
#                         price=int(temp['price']),
#                         q10_category=temp['q10_category'],
#                         point=int(temp['point']),
#                         variation_options=temp['relationships'],
#                         base_name=temp['base_name'],
#                         base_asin=temp['original_asin']
#                     ).save()
#                     to_transfer_list.append(key)
#                 except Exception as e:
#                     import json
#                     log_failed_asin_list.append([key, json.dumps(temp)])
#                     print('追加失敗ASIN：', key)
#             else:
#                 # log_failed_asin_list.append(key)
#                 to_transfer_list.append(key)
#         print('追加完了')
#     else:
#         print('search_listが空なためasin_listに直で追加します。')
#
#     to_transfer_list.extend(to_list_but_still_in_waiting)
#     to_transfer_list = list(filter(None, to_transfer_list))
#
#     # 出品→asin_waitingからasin_listに移す
#     print(to_transfer_list)
#     for asin in to_transfer_list:
#         ok, reason = upload_new_item(asin, username, certification_key)
#         print(ok, reason)
#         if ok:
#             print(variation_asins)
#             if asin in variation_asins.keys():
#                 to_del_asin = variation_asins[asin]
#                 print(to_del_asin)
#             else:
#                 to_del_asin = asin
#             try:
#                 asin_waiting_list.remove(to_del_asin)
#             except:
#                 pass
#
#             try:
#                 asin_getting_list.remove(to_del_asin)
#             except:
#                 pass
#
#             asin_list.append(asin)
#             selling_list.append(asin)
#             log_success_asin_list.append(asin)
#         else:
#             log_failed_asin_list.append([asin, reason])
#
#             if reason != '出品失敗':
#                 try:
#                     asin_waiting_list.remove(asin)
#                 except:
#                     pass
#
#     obj.asin_list = ','.join(list(filter(None, asin_list)))
#     obj.selling_list = ','.join(list(filter(None, selling_list)))
#     obj.asin_waiting_list = ','.join(list(filter(None, asin_waiting_list)))
#     obj.asin_getting_list = ','.join([val for val in obj.asin_getting_list.split(',') if val not in new_getting_list])
#     obj.save()
#
#     corresponding_record_object.already_listed = True
#     corresponding_record_object.status_text = ''
#     corresponding_record_object.save()
#
#     # 失敗理由リスト　区切り単語："delimiter"
#     temp = [val[0] for val in log_failed_asin_list]
#     log_total_list = temp
#     log_total_list.extend(log_success_asin_list)
#     cause_list = ''
#     for val in log_failed_asin_list:
#         cause_list += f'{val[0]}:{val[1]}{delimiter}'
#     LogModel(username=username, type='出品', input_asin_list=','.join(log_total_list),
#              success_asin_list=','.join(log_success_asin_list), cause_list=cause_list,
#              date=datetime.datetime.now()).save()
#
#     print('完了')


# アカウントリンク
@shared_task
def link_q10_account(username):
    """
    ListingModel上でusernameに対応するasin_listに追加していく。
    """
    certification_key = get_certification_key(username)

    link_q10_items(certification_key, username)


# データベース価格改定
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

            price, point = sp_api.get_lowest_price(offers.payload)

            if price:
                add_log(True, obj.asin)
                obj.price = int(price)
                obj.point = int(point)
            else:
                obj.price = 0
                obj.point = 0
                add_log(False, obj.asin, point)

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


# 商品削除
@shared_task
def delete_items(username, to_delete_asin_list):
    obj: ListingModel = ListingModel.objects.get(username=username)
    obj.asin_list = ','.join(list(dict.fromkeys(obj.asin_list.split(','))))
    obj.save()
    selling_list = obj.selling_list.split(',')
    no_stock_list = obj.no_stock_list.split(',')
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
            selling_list.remove(asin) if asin in selling_list else selling_list
            obj.selling_list = ','.join(selling_list)
            no_stock_list.remove(asin) if asin in no_stock_list else no_stock_list
            obj.no_stock_list = ','.join(no_stock_list)
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


# ユーザー価格改定
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


# データベースバックアップ＆要らないデータを削除
@shared_task
def backup_clean_up():
    now = datetime.datetime.now().replace(tzinfo=pytz.UTC)

    # Remove records data
    objects = RecordsModel.objects.all()
    try:
        for obj in chunked(objects):
            try:
                if (now - obj.date).days >= 10:
                    obj.delete()
            except:
                pass
    except RuntimeError:
        pass

    try:
        objects = LogModel.objects.all()
        for obj in chunked(objects):
            try:
                if (now - obj.date).days >= 10:
                    obj.delete()
            except:
                pass
    except RuntimeError:
        pass


def chunked(queryset, chunk_size=1000):
    start = 0
    while True:
        chunk = queryset[start:start + chunk_size]
        for obj in chunk:
            yield obj
        if len(chunk) < chunk_size:
            raise StopIteration
        start += chunk_size

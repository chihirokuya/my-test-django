from __future__ import absolute_import, unicode_literals
from celery import shared_task
import time
from list_price_revision.models import ListingModel, RecordsModel, AsinModel
import threading
from list_price_revision.api import get_info_from_amazon


@shared_task
def records_saved(username, date):
    """
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

    asin_waiting_list: list = list(obj.asin_waiting_list.split(','))
    asin_list = list(obj.asin_list.split(','))
    asin_getting_list = list(obj.asin_getting_list.split(','))

    new_getting_list = []

    to_search_list = []
    for asin in asin_waiting_list:
        if not AsinModel.objects.filter(asin=asin).exists() and asin not in asin_getting_list:
            to_search_list.append(asin)
        else:
            asin_getting_list.append(asin)
            asin_waiting_list.remove(asin)
            asin_list.append(asin)
            new_getting_list.append(asin)

    obj.asin_getting_list = ','.join(asin_getting_list)
    obj.save()

    print('search_list', to_search_list)
    print('asin_list', obj.asin_list)
    print('asin_waiting_list', obj.asin_waiting_list)

    to_transfer_list = []

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

        print('divided_list', divided_list)

        threads = []
        to_search_class = ToSearchThread
        for i in range(thread_num):
            threads.append(threading.Thread(
                target=get_info_from_amazon,
                kwargs={
                    "to_search_class": to_search_class,
                    'asin_list': divided_list[i]
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


    # 出品→asin_waitingからasin_listに移す
    for asin in to_transfer_list:
        # TODO
        try:
            asin_waiting_list.remove(asin)
        except:
            pass

        asin_list.append(asin)

    obj.asin_list = ','.join(list(filter(None, asin_list)))
    obj.asin_waiting_list = ','.join(list(filter(None, asin_waiting_list)))
    obj.asin_getting_list = ','.join([val for val in obj.asin_getting_list.split(',') if val not in new_getting_list])
    obj.save()

    corresponding_record_object.already_listed = True
    corresponding_record_object.save()

    print('完了')
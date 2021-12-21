from mysite.settings import MEDIA_ROOT
from django.shortcuts import render, redirect, reverse, HttpResponse
from .models import UserModel, AsinModel, RecordsModel, ListingModel
from .api import get_info_from_amazon
from django.contrib import messages
import datetime
import os
import pytz
import csv
import threading
from mysite.tasks import records_saved

base_path = 'list_price_revision/'

"""
ページ関連
"""


def base_view(request):
    if not ListingModel.objects.filter(username=request.user).exists():
        ListingModel(username=request.user).save()
    list_obj = ListingModel.objects.get(username=request.user)
    asin_list = list_obj.asin_list.split(',')

    context = {
        "asin_list_length": len(asin_list)
    }
    return render(request, base_path + 'start_page.html', context)


def asin_view(request):
    # obj = UserModel.objects.get(username=request.user)

    if not ListingModel.objects.filter(username=request.user).exists():
        ListingModel(username=request.user).save()

    list_obj = ListingModel.objects.get(username=request.user)

    pre_asin_list = ''
    records = []

    if request.method == 'POST':
        if 'asin_upload' in request.POST:
            """
            まず空＆ASIN以外を削除。からでなければ次へ
            tempからasin_waiting_listまたはasin_listに入っているものは削除。
            asin_waiting_listを保存。
            """
            try:
                print('request.post asin_list', request.POST['asin_list'].split('\n'))

                # まず空＆ASINでないものを削除
                temp = [val.rstrip() for val in list(filter(None, request.POST['asin_list'].split('\n'))) if
                        len(val.rstrip()) == 10 and val[0].upper() == 'B']

                print('temp', temp)

                if temp:
                    asin_list = list_obj.asin_list.split(',')
                    try:
                        asin_waiting_list = list_obj.asin_waiting_list.split(',')
                    except:
                        asin_waiting_list = []

                    old_length = len(temp)

                    temp = [val for val in temp if val not in asin_list and val not in asin_waiting_list]

                    asin_waiting_list.extend(temp)
                    list_obj.asin_waiting_list = ','.join(list(dict.fromkeys(list(filter(None, asin_waiting_list)))))
                    date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))

                    new_records = RecordsModel(
                        username=request.user,
                        date=date,
                        total_length=old_length,
                        new_length=len(temp),
                        already_listed=len(temp) == 0,
                        asin_list=','.join(temp)
                    )

                    list_obj.save()
                    new_records.save()

                    records_saved.delay(str(request.user), date)

                    messages.success(request, '正常に更新されました。')
                    records = []
                else:
                    messages.error(request, '有効なASINが見つかりませんでした。')
            except:
                messages.error(request, '問題が発生しました。')

        elif 'csv_upload' in request.FILES.keys():
            try:
                csv_file = request.FILES["csv_upload"]
                folder_dir = MEDIA_ROOT + f'/{request.user}'
                file_path = folder_dir + f'/{csv_file.name}.csv'

                if not os.path.isdir(folder_dir):
                    os.mkdir(folder_dir)

                with open(file_path, "wb+") as f:
                    f.write(csv_file.read())

                with open(file_path, 'r', encoding='shift-jis', errors='ignore') as file:
                    pre_asin_list = [val[0] for val in csv.reader(file) if val and len(val[0]) == 10]

                pre_asin_list = '\n'.join(pre_asin_list)
                os.remove(file_path)
            except:
                messages.error(request, 'CSVファイルでない、またはエンコードがSHIFT-JISでない可能性があります。')

    records_obj = RecordsModel.objects.all().filter(username=request.user).order_by('-date')
    for obj_ in records_obj:
        records.append([obj_.date, obj_.total_length, obj_.new_length, obj_.already_listed])
    context = {
        "pre_asin_list": pre_asin_list,
        "records": records,
        'waiting_list': '\n'.join(list_obj.asin_waiting_list.split(','))
    }
    return render(request, base_path + 'asin_page.html', context)


def listing_view(request):
    if not ListingModel.objects.filter(username=request.user).exists():
        ListingModel(username=request.user).save()
    list_obj = ListingModel.objects.get(username=request.user)
    asin_list = list_obj.asin_list.split(',')

    info_list = []
    for asin in asin_list:
        try:
            temp_obj = AsinModel.objects.get(asin=asin)

            img = temp_obj.photo_list.split('\n')[0]
            name = temp_obj.product_name
            brand = temp_obj.brand
            description = temp_obj.description
            jan = temp_obj.jan
            price = temp_obj.price

            info_list.append([img, asin, price, name, jan, brand, description])
        except:
            pass

    context = {
        "info_list": info_list
    }

    return render(request, base_path + 'listing-items.html', context)


def blacklist_view(request):
    amazon_group_list = ['Alcoholic Beverage', 'Amazon SMP', 'Amazon Tablets', 'Apparel', 'Art and Craft Supply',
                         'Authority Non Buyable', 'Automotive Parts and Accessories', 'Baby Product', 'Beauty', 'BISS',
                         'BISS Basic', 'Book', 'CE', 'Digital Accessories 3', 'Digital Accessories 4',
                         'Digital Device Accessory', 'DVD', 'Fabric', 'GPS or Navigation System', 'Grocery',
                         'Hand Tools', 'Health and Beauty', 'Hobby', 'Home', 'Home Improvement', 'Home Theater',
                         'Jewelry', 'Kitchen', 'Lawn & Patio', 'Lighting', 'Luggage', 'Major Appliances', 'MotorCycle',
                         'Music', 'Musical Instruments', 'Office Product', 'Pantry', 'PC Accessory',
                         'Personal Computer', 'Pet Products', 'Photography', 'Premium Consumer Electronics Brands',
                         'Prestige Beauty', 'Receiver or Amplifier', 'Shoes', 'Single Detail Page Misc', 'Software',
                         'Speakers', 'Sports', 'Toy', 'Video', 'Video Games', 'Watch', 'Wireless',
                         'Wireless Phone Accessory']
    obj = UserModel.objects.get(username=request.user)

    context = {
        'amazon_group_list': amazon_group_list,
        'obj': obj,
        'amazon_group_blacklist': obj.group_black.split(','),
    }

    if request.method == 'POST':
        temp = request.POST

        try:
            obj.maker_name_blacklist = temp['maker_name_blacklist']
            obj.asin_blacklist = temp['asin_blacklist']
            obj.words_blacklist = temp['words_blacklist']

            # 商品グループについて
            amazon_group_blacklist = []
            for group in amazon_group_list:
                if group in temp.keys():
                    amazon_group_blacklist.append(group)
            obj.group_black = ','.join(amazon_group_blacklist)

            obj.save()
            messages.success(request, '情報が更新されました')

        except:
            messages.error(request, '保存内容に誤りがあります。')

        return redirect(reverse('price:blacklist'))

    return render(request, base_path + 'blacklist.html', context)


def setting_view(request):
    obj = UserModel.objects.get(username=request.user)
    context = {
        'obj': obj,
        'alphabets': [chr(i) for i in list(range(65, 91))],
        'alert': False
    }

    if request.method == 'POST':
        temp = request.POST
        try:
            obj.q10_id = temp['q10_id']
            obj.q10_password = temp['q10_password']
            obj.description_header = temp['description_header']
            obj.description_footer = temp['description_footer']
            obj.initial_letter = temp['initial_letter']
            obj.delete_or_not = True if 'delete_or_not' in temp.keys() else False
            obj.shipping_code = temp['shipping_code']
            obj.stock_num = int(temp['stock_num'])
            obj.photo_num = int(temp['photo_num'])
            obj.max_1 = int(temp['max_1'])
            obj.max_2 = int(temp['max_2'])
            obj.max_3 = int(temp['max_3'])
            obj.rieki_1 = int(temp['rieki_1'])
            obj.rieki_2 = int(temp['rieki_2'])
            obj.rieki_3 = int(temp['rieki_3'])
            obj.rieki_4 = int(temp['rieki_4'])
            obj.kotei_1 = int(temp['kotei_1'])
            obj.kotei_2 = int(temp['kotei_2'])
            obj.kotei_3 = int(temp['kotei_3'])
            obj.kotei_4 = int(temp['kotei_4'])
            obj.kaitei_kankaku = datetime.time(int(temp['kaitei_hour']), int(temp['kaitei_minute']))
            obj.save()

            messages.success(request, '情報が更新されました')

            return redirect(reverse('price:setting'))
        except:
            messages.error(request, '保存内容に誤りがあります。')
            return redirect(reverse('price:setting'))

    return render(request, base_path + 'setting.html', context)


from django.db.models.signals import post_save
from django.dispatch import receiver

"""
API系
"""


# @receiver(post_save, sender=RecordsModel)
# def pre_save_func(sender, instance, created, **kwargs):
#     """
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
#     # 新規作成でないなら何もしない
#     if not created:
#         return
#
#     username = instance.username
#
#     obj = ListingModel.objects.get(username=username)
#     corresponding_record_object = RecordsModel.objects.get(username=username, date=instance.date)
#
#     print(obj.asin_list, obj.asin_waiting_list)
#
#     asin_waiting_list: list = list(obj.asin_waiting_list.split(','))
#     asin_list = list(obj.asin_list.split(','))
#
#     to_search_list = []
#     for asin in asin_waiting_list:
#         if not AsinModel.objects.filter(asin=asin).exists():
#             to_search_list.append(asin)
#
#     print('search_list', to_search_list)
#
#
#
#     # 個数を確認し、5個またはそれ以下のThreadを作成
#     class ToSearchThread:
#         result_list = {}
#         to_delete_asin_list = []
#
#         def __init__(self):
#             self.result_list = {}
#             self.to_delete_asin_list = []
#
#     if len(to_search_list) > 10:
#         thread_num = 5
#     else:
#         thread_num = 1
#
#     length = len(to_search_list) // thread_num
#     divided_list = [to_search_list[i * length: (i + 1) * length] for i in range(thread_num - 1)]
#     divided_list.append(to_search_list[(thread_num - 1) * length:])
#
#     print('divided_list', divided_list)
#
#     threads = []
#     to_search_class = ToSearchThread
#     for i in range(thread_num):
#         threads.append(threading.Thread(
#             target=get_info_from_amazon,
#             kwargs={
#                 "to_search_class": to_search_class,
#                 'asin_list': divided_list[i]
#             }
#         ))
#
#     for thread in threads:
#         thread.start()
#     for thread in threads:
#         thread.join()
#
#     print('削除開始')
#     print(to_search_class.to_delete_asin_list)
#     print(to_search_class.result_list)
#     # DeleteListを参考にasin_waiting_listから削除していく
#     for asin in to_search_class.to_delete_asin_list:
#         try:
#             asin_waiting_list.remove(asin)
#         except:
#             pass
#     print('削除完了')
#
#     print('ASINモデル追加開始')
#     # ASINモデルを追加していく
#     for key in to_search_class.result_list.keys():
#         if not AsinModel.objects.filter(asin=key).exists():
#             try:
#                 temp = to_search_class.result_list[key]
#                 AsinModel(
#                     asin=key,
#                     product_name=temp['name'],
#                     brand=temp['brand'],
#                     product_group=temp['group'],
#                     photo_list='\n'.join(temp['links']),
#                     description='\n'.join(temp['description']),
#                     jan=temp['jan'],
#                     category_tree=temp['category_tree'],
#                     price=int(temp['price'])
#                 ).save()
#             except:
#                 print(key, '失敗')
#     print('追加完了')
#
#
#     # 出品→asin_waitingからasin_listに移す
#     for asin in asin_waiting_list:
#         # TODO
#         try:
#             asin_waiting_list.remove(asin)
#         except:
#             pass
#
#         asin_list.append(asin)
#
#     obj.asin_list = ','.join(asin_list)
#     obj.asin_waiting_list = ','.join(asin_waiting_list)
#     obj.save()
#
#     corresponding_record_object.already_listed = True
#     corresponding_record_object.save()
#
#     print('完了')
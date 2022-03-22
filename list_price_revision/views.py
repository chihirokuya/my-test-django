import time
from mysite.settings import MEDIA_ROOT
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.http import JsonResponse
from .models import UserModel, AsinModel, RecordsModel, ListingModel, Q10ItemsLink, Q10BrandCode, LogModel, delimiter
from .api import get_info_from_amazon, to_user_price, get_certification_key, get_cat_from_csv, user_price_and_profit, is_in_black, get_new_orders
from django.contrib import messages
import datetime
import os
import pytz
import csv
import threading
from dateutil import tz
from mysite.tasks import records_saved, link_q10_account, re_price_users
from mysite import tasks
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializer import AsinSerializer
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from autobuy.models import AsinSalesModel
from autobuy.models import OrderModel


base_path = 'list_price_revision/'

"""
ページ関連
"""


def base_view(request):
    if not ListingModel.objects.filter(username=request.user).exists():
        ListingModel(username=request.user).save()
    list_obj = ListingModel.objects.get(username=request.user)
    asin_list = list_obj.asin_list.split(',')

    if not Q10ItemsLink.objects.filter(username=request.user).exists():
        Q10ItemsLink(username=request.user).save()
    q10_obj: Q10ItemsLink = Q10ItemsLink.objects.get(username=request.user)
    total_asin_list = list(filter(None, q10_obj.total_asin_list.split(',')))
    linked_asin_list = list(filter(None, q10_obj.linked_asin_list.split(',')))

    user_obj: UserModel = UserModel.objects.get(username=request.user)

    if request.method == 'POST':
        if 'link_button' in request.POST:
            if not q10_obj.still_getting:
                link_q10_account.delay(str(request.user))

                messages.success(request, 'リンクが開始しました。ページを再読み込みする事により進捗状況を更新できます。')

        list_obj = ListingModel.objects.get(username=request.user)
        asin_list = list_obj.asin_list.split(',')
        q10_obj: Q10ItemsLink = Q10ItemsLink.objects.get(username=request.user)
        total_asin_list = list(filter(None, q10_obj.total_asin_list.split(',')))
        linked_asin_list = list(filter(None, q10_obj.linked_asin_list.split(',')))

    context = {
        'obj': user_obj,
        "asin_list_length": len(asin_list),
        "total_length": len(total_asin_list),
        "linked_length": len(linked_asin_list),
        "percentage": int(len(linked_asin_list) / len(total_asin_list)) * 100 if len(total_asin_list) != 0 else 100,
        "api_ok": user_obj.api_ok,
        "still_getting": q10_obj.still_getting
    }

    return render(request, base_path + 'start_page.html', context)


def asin_view(request):
    user_obj = UserModel.objects.get(username=request.user)

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
                        asin_list=','.join(temp),
                        status_text='取得を開始します。'
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

                with open(file_path, "wb") as f:
                    f.write(csv_file.read())

                with open(file_path, 'r', encoding='shift-jis', errors='ignore') as file:
                    pre_asin_list = [val[0] for val in csv.reader(file) if val and len(val[0]) == 10]

                pre_asin_list = '\n'.join(pre_asin_list)
                os.remove(file_path)
            except:
                messages.error(request, 'CSVファイルでない、またはエンコードがSHIFT-JISでない可能性があります。')

        elif 'clean' in request.POST:
            try:
                list_obj.asin_waiting_list = ''
                list_obj.asin_getting_list = ''
                list_obj.save()

                records = RecordsModel.objects.filter(username=request.user)
                try:
                    for rec in chunked(records):
                        rec.delete()
                except:
                    pass

                messages.success(request, '削除完了')
            except Exception as e:
                messages.error(request, f'削除失敗\n{str(e)}')

    records_obj = RecordsModel.objects.all().filter(username=request.user).order_by('-date')
    try:
        for obj_ in chunked(records_obj):
            records.append([obj_.date, obj_.total_length, obj_.new_length, obj_.already_listed, obj_.status_text])
    except RuntimeError:
        pass

    context = {
        'obj': user_obj,
        "pre_asin_list": pre_asin_list,
        "records": records,
        'waiting_list': '\n'.join(list_obj.asin_waiting_list.split(',')),
    }
    return render(request, base_path + 'asin_page.html', context)


def listing_view(request):
    context = {
        "obj": UserModel.objects.get(username=request.user),
        "info_list": [],
        'username': str(request.user)
    }

    # print(f'{time.perf_counter() - start}秒で完了しました。')

    if request.method == "POST":
        if 'asin_list' in request.POST:
            try:
                to_delete_asin_list = request.POST['asin_list'].split(',')

                tasks.delete_items.delay(str(request.user), to_delete_asin_list)

                messages.success(request, '削除が開始されました。')
            except Exception as e:
                messages.error(request, '内部エラーが発生しました。\n' + f'{e}')

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
    if not UserModel.objects.filter(username='admin').exists():
        UserModel(username='admin').save()

    ad_obj = UserModel.objects.get(username='admin')

    context = {
        'amazon_group_list': amazon_group_list,
        'obj': ad_obj,
        'amazon_group_blacklist': obj.group_black.split(','),
        'maker': ad_obj.maker_name_blacklist.split('\n'),
        'asins': ad_obj.asin_blacklist.split('\n'),
        'words': ad_obj.words_blacklist.split('\n')
    }

    if request.method == 'POST':
        temp = request.POST

        try:
            current_name_blacklist = ad_obj.maker_name_blacklist.split('\n')
            current_name_blacklist.extend(temp['maker_name_blacklist'].split('\n'))
            ad_obj.maker_name_blacklist = '\n'.join([val.strip() for val in list(dict.fromkeys(current_name_blacklist))])

            current_asin_blacklist = ad_obj.asin_blacklist.split('\n')
            current_asin_blacklist.extend(temp['asin_blacklist'].split('\n'))
            ad_obj.asin_blacklist = '\n'.join(list(dict.fromkeys(current_asin_blacklist)))

            current_words_blacklist = ad_obj.words_blacklist.split('\n')
            current_words_blacklist.extend(temp['words_blacklist'].split('\n'))
            ad_obj.words_blacklist = '\n'.join(list(dict.fromkeys(current_words_blacklist)))

            # 商品グループについて
            amazon_group_blacklist = []
            for group in amazon_group_list:
                if group in temp.keys():
                    amazon_group_blacklist.append(group)
            obj.group_black = ','.join(amazon_group_blacklist)

            obj.save()
            ad_obj.save()
            messages.success(request, '情報が更新されました')

        except Exception as e:
            messages.error(request, f'保存内容に誤りがあります。{e}')

        return redirect(reverse('price:blacklist'))

    return render(request, base_path + 'blacklist.html', context)


def setting_view(request):
    obj: UserModel = UserModel.objects.get(username=request.user)
    context = {
        'obj': obj,
        'alphabets': [chr(i) for i in list(range(65, 91))],
        'alert': False
    }

    if request.method == 'POST':
        temp = request.POST
        if 'q10_id' in temp:
            try:
                obj.q10_id = temp['q10_id']
                obj.q10_password = temp['q10_password']
                obj.q10_api = temp['q10_api']
                obj.description_header = temp['description_header']
                obj.description_footer = temp['description_footer']
                obj.initial_letter = temp['initial_letter']
                obj.delete_or_not = True if 'delete_or_not' in temp.keys() else False
                obj.shipping_code = temp['shipping_code']
                obj.stock_num = int(temp['stock_num'])
                obj.photo_num = int(temp['photo_num'])
                obj.min_1 = int(temp['min_1'])
                obj.max_1 = int(temp['max_1'])
                obj.max_2 = int(temp['max_2'])
                obj.max_3 = int(temp['max_3'])
                obj.max_4 = int(temp['max_4'])
                obj.rieki_1 = int(temp['rieki_1'])
                obj.rieki_2 = int(temp['rieki_2'])
                obj.rieki_3 = int(temp['rieki_3'])
                obj.rieki_4 = int(temp['rieki_4'])
                obj.kotei_1 = int(temp['kotei_1'])
                obj.kotei_2 = int(temp['kotei_2'])
                obj.kotei_3 = int(temp['kotei_3'])
                obj.kotei_4 = int(temp['kotei_4'])
                obj.shop_name = temp['shop_name']
                obj.save()

                messages.success(request, '情報が更新されました')
            except:
                messages.error(request, '保存内容に誤りがあります。')
        elif 'check_api' in temp:
            try:
                obj.q10_id = temp['acc_id']
                obj.q10_password = temp['acc_pass']
                obj.q10_api = temp['acc_api']
                obj.save()

                cert_key = get_certification_key(str(request.user))

                if not cert_key:
                    obj.api_ok = False
                    messages.error(request, '接続に失敗しました。')
                else:
                    obj.api_ok = True
                    messages.success(request, '接続に成功しました')

                obj.save()
            except:
                messages.error(request, 'エラーが発生しました。')

        return redirect(reverse('price:setting'))

    return render(request, base_path + 'setting.html', context)


def log_view(request):
    context = {
        "obj": UserModel.objects.get(username=request.user)
    }
    return render(request, base_path + 'log_page.html', context)


def chunked(queryset, chunk_size=1000):
    start = 0
    while True:
        chunk = queryset[start:start + chunk_size]
        for obj in chunk:
            yield obj
        if len(chunk) < chunk_size:
            raise StopIteration
        start += chunk_size



# 軽API
def get_log(request, range=1):
    start_date = (datetime.datetime.now() - datetime.timedelta(days=range)).strftime('%Y-%m-%d')
    end_date = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    log_obj_list = LogModel.objects.filter(username=request.user, date__range=[start_date, end_date])

    # id, 日付、動作内容、成功ASIN数、失敗ASIN数
    res_list = []
    # id, 成功ASINリスト、[[失敗ASIN、理由]]
    res_list_no_date = []
    id_ = 1
    try:
        for obj in chunked(log_obj_list):
            obj: LogModel
            total_asin_list = list(filter(None, obj.input_asin_list.split(',')))
            if delimiter not in obj.success_asin_list:
                success_asin_list = list(filter(None, obj.success_asin_list.split(',')))
            else:
                success_asin_list = []
                for val in obj.success_asin_list.split(delimiter):
                    temp = val.split(':')
                    try:
                        success_asin_list.append([temp[0], temp[1]])
                    except:
                        pass

            failed_list = []
            for val in obj.cause_list.split(delimiter):
                temp = val.split(':')
                try:
                    failed_list.append([temp[0], temp[1]])
                except:
                    pass

            res_list.append(
                [id_, obj.date.astimezone(tz.gettz('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M'), obj.type, len(success_asin_list), len(total_asin_list) - len(success_asin_list)])
            res_list_no_date.append([id_, success_asin_list, failed_list])
            id_ += 1
    except RuntimeError:
        pass

    res_list.sort(key=lambda x: x[1], reverse=True)

    context = {
        "res_list": res_list,
        "no_date": res_list_no_date
    }

    return JsonResponse(context)


def get_table(request):
    username = request.user

    try:
        sales_list = AsinSalesModel.objects.get(user=User.objects.get(username=username)).sales_list
    except:
        sales_list = {}

    if not ListingModel.objects.filter(username=username).exists():
        ListingModel(username=request.user).save()
    list_obj = ListingModel.objects.get(username=username)
    asin_list = list_obj.asin_list.split(',')
    user_obj: UserModel = UserModel.objects.get(username=username)

    start = time.perf_counter()
    info_json_list = []
    category_list = {}
    print('select start')
    all_objects = AsinModel.objects.filter(asin__in=asin_list)
    print('select finished')
    try:
        for temp_obj in chunked(all_objects):
            temp_obj: AsinModel
            img = temp_obj.photo_list.split('\n')[0]
            name = temp_obj.product_name
            try:
                brand_obj: Q10BrandCode = Q10BrandCode.objects.get(code=temp_obj.brand)
                brand = brand_obj.brand_name
            except:
                brand = ''
            user_price, profit = user_price_and_profit(user_obj, temp_obj.price)
            point = temp_obj.point
            category = temp_obj.q10_category

            if category not in category_list.keys():
                category_list[category] = 1
            else:
                category_list[category] += 1

            sell_num = 0
            if temp_obj.asin in sales_list.keys():
                sell_num = sales_list[temp_obj.asin]

            info_json_list.append({
                'asin': temp_obj.asin,
                'img_link': img,
                "product_name": name,
                "brand": brand,
                "price": user_price,
                "amazon_price": temp_obj.price,
                "point": point,
                "category": category,
                "profit": profit,
                "sell_num": sell_num
            })
    except RuntimeError:
        pass

    print(f'{time.perf_counter()-start}秒')

    with open(MEDIA_ROOT + '/categories.csv', 'r', encoding='utf-8_sig',
              errors='ignore') as f:
        categories = [r for r in csv.reader(f) if r and r[0] != '']

    key_list = list(category_list.keys())
    total_list = {}
    sub_category_names = {}

    for cat in categories:
        if cat[4] in key_list:
            top_num = cat[0]
            top_name = cat[1]
            mid_num = cat[2]
            mid_name = cat[3]
            sub_num = cat[4]
            sub_name = cat[5]

            sub_category_names[sub_num] = top_name + '<p>' + mid_name + '<p>' + sub_name

            num = category_list[sub_num]

            if top_num not in total_list.keys():
                total_list[top_num] = {
                    'num': num,
                    'name': top_name,
                    mid_num: {
                        "num": num,
                        "name": mid_name,
                        sub_num: {
                            "num": num,
                            "name": sub_name
                        }
                    }
                }
            else:
                total_list[top_num]['num'] += num

                if mid_num not in total_list[top_num].keys():
                    total_list[top_num][mid_num] = {
                        "num": num,
                        "name": mid_name,
                        sub_num: {
                            "num": num,
                            "name": sub_name
                        }
                    }
                else:
                    total_list[top_num][mid_num]['num'] += num

                    if sub_num not in total_list[top_num][mid_num].keys():
                        total_list[top_num][mid_num][sub_num] = {
                            "num": num,
                            "name": sub_name
                        }
                    else:
                        total_list[top_num][mid_num][sub_num]['num'] += num

    return JsonResponse({"cat": total_list, "info_json": info_json_list, 'sub_names': sub_category_names})


def sell_and_not_stock(request):
    username = request.user

    if not ListingModel.objects.filter(username=username).exists():
        ListingModel(username=request.user).save()
    list_obj = ListingModel.objects.get(username=username)

    selling_num = len(list_obj.selling_list.split(','))
    no_stock_num = len(list_obj.no_stock_list.split(','))
    a = 1
    get_new_orders(username)

    if not OrderModel.objects.filter(username=username).exists():
        OrderModel(username=username).save()
    order_obj = OrderModel.objects.get(username=username)
    new = len(order_obj.order_list)
    failed = len(order_obj.failed_order_list)

    return JsonResponse({"selling_num": selling_num, "no_stock_num": no_stock_num,
                         "new": new, "failed": failed})


@csrf_exempt
def update_user_price(request):
    try:
        re_price_users.delay()
    except:
        return JsonResponse({'ok': False})

    return JsonResponse({'ok': True})



@api_view(['GET'])
def get_asin_data(request):
    list_obj = ListingModel.objects.get(username=request.user)
    asin_list = list_obj.asin_list.split(',')

    items = AsinModel.objects.filter(asin__in=asin_list)
    # items = AsinModel.objects.all()
    serializer = AsinSerializer(items, many=True)

    return Response(serializer.data)
import datetime
import json
from django.shortcuts import render, HttpResponse
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.decorators import api_view
import list_price_revision
from . import models
from list_price_revision.models import UserModel
from list_price_revision.views import chunked
from list_price_revision import api
from django.contrib import messages
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from .serializer import BuyUserSerializer, SingleSaleSerializer
from rest_framework.response import Response
import requests
from django.shortcuts import get_object_or_404


base_path = 'autobuy/'


def assert_existence_of_user(username):
    if not models.BuyUserModel.objects.filter(username=username).exists():
        models.BuyUserModel(username=username).save()


def assert_existence_of_order_model(username):
    if not models.OrderModel.objects.filter(username=username).exists():
        models.OrderModel(username=username, order_list=[]).save()


def order_view(request):
    try:
        user_obj = UserModel.objects.get(username=request.user)
    except:
        user_obj = None

    context = {
        "obj": user_obj,
        'user': request.user
    }
    return render(request, base_path + 'order_page.html', context)


def setting_view(request):
    assert_existence_of_user(request.user)
    buy_obj: models.BuyUserModel = models.BuyUserModel.objects.get(username=request.user)

    if request.method == 'POST':
        try:
            if type(request.body) == bytes:
                res = json.loads(request.body)['data']
            else:
                res = request.body['data']

            buy_obj.mail_address = res['mail_address']
            buy_obj.mail_pass = res['mail_pass']
            buy_obj.credit_card = res['credit_card']
            buy_obj.name = res['name']
            buy_obj.post_num = res['post_num']
            buy_obj.prefecture = res['prefecture']
            buy_obj.address = res['address']
            buy_obj.phone_num = res['phone_num']
            buy_obj.mega_wari = res['mega_wari']
            buy_obj.point = res['point']
            buy_obj.akaji = int(res['akaji'])
            buy_obj.cancel_message = res['cancel_message']
            buy_obj.company_name = res['company_name']
            buy_obj.gift = res['gift']
            proxy_list = []
            for proxy in res['proxy_list']:
                proxy_list.append({
                    "ip": proxy[0],
                    "port": proxy[1],
                    "id": proxy[2],
                    "password": proxy[3],
                })

            buy_obj.proxy = proxy_list
            buy_obj.save()

            return JsonResponse({'ok': True})
        except Exception as e:
            print('here')
            return JsonResponse({"ok": False, "reason": str(e)})

    post_nums = buy_obj.post_num.split('-')

    if len(post_nums) == 1:
        post_nums.append('')

    proxy_list = []
    for proxy in buy_obj.proxy:
        proxy_list.append(list(proxy.values()))

    context = {
        "obj": UserModel.objects.get(username=request.user),
        "buy_obj": buy_obj,
        "post_1": post_nums[0],
        'post_2': post_nums[1],
        "proxy_list": proxy_list
    }

    return render(request, base_path + 'setting.html', context)


def delivered_view(request):
    li = models.DeliveredOrderModel.objects.filter(user=request.user)

    print(li)

    return HttpResponse(f'{li[0].delivered_date}')


def profit_table_view(request):
    user_model = User.objects.get(username=request.user)

    context = {
        "obj": UserModel.objects.get(username=request.user),
        "month_list": list(range(1, 100))
    }
    return render(request, base_path + 'profit_table.html', context)



# 軽API
def assert_user_pass(request):
    if request.method == 'GET':
        temp = request.GET
    else:
        temp = request.POST if 'username' in request.POST else json.loads(request.body)

    if 'username' in temp and 'password' in temp:
        user_name = temp['username']
        password = temp['password']

        return authenticate(request, username=user_name, password=password) is not None

    return False


def assert_sales_model(username):
    if not models.SalesModel.objects.filter(user=User.objects.get(username=username)).exists():
        models.SalesModel(user=User.objects.get(username=username)).save()


def update_orders(order_obj, username, order_number_list):
    assert_sales_model(username)

    sales_obj = models.SalesModel.objects.get(user=User.objects.get(username=username))

    failed_order_nums = [val['orderNo'] for val in order_obj.failed_order_list]
    try:
        res = api.get_new_orders(username)
        key_list = []
        for val in res:
            if not sales_obj.singlesalemodel_set.filter(order_num=val['orderNo']).exists():
                key_list.append(val['orderNo'])
            if val['orderNo'] not in order_number_list and val['orderNo'] not in failed_order_nums:
                order_obj.order_list.append(val)

        order_obj.order_list = [val for val in order_obj.order_list if val['orderNo'] in key_list]
        order_obj.save()
    except Exception as e:
        print(e)

    return


def order_page_api(request, mode):
    if request.method == 'GET' and 'username' in request.GET:
        username = request.GET['username']
    else:
        if request.method == 'POST' and 'username' in request.POST:
            username = request.POST['username']
        else:
            username = request.user

    assert_existence_of_order_model(str(username))

    order_obj: models.OrderModel = models.OrderModel.objects.get(username=username)

    order_list = {}
    failed_list = {}

    if request.method == 'GET':
        for val in order_obj.order_list:
            order_list[val['orderNo']] = {
                "date": val['orderDate'],
                "prod_name": val['itemTitle'],
                "qty": val['orderQty'],
                "name": val['receiver'],
                "phone_num": val['receiverTel'],
                "mobile_num": val['receiverMobile'],
                "address": val['shippingAddr'],
                "zip_code": val['zipCode'],
                "total": val['total'],
                "item_code": val['sellerItemCode']
            }

        for val in order_obj.failed_order_list:
            failed_list[val['orderNo']] = {
                "reason": val['reason'],
                "date": val['orderDate'],
                "qty": val['orderQty'],
                "name": val['receiver'],
                "phone_num": val['receiverTel'],
                "mobile_num": val['receiverMobile'],
                "address": val['shippingAddr'],
                "zip_code": val['zipCode'],
                "total": val['total'],
                "item_code": val['sellerItemCode'],
                "prod_name": val['itemTitle'],
            }

        if mode == 0:
            return JsonResponse({"order_list": order_list, "failed_list": failed_list})
        else:
            order_number_list = list(order_list.keys())

            update_orders(order_obj, str(username), order_number_list)

            return HttpResponse()
    else:
        try:
            if type(request.body) == bytes:
                res = json.loads(request.body)['data']
            else:
                res = request.body['data']
        except:
            res = []

        order_obj.order_list = [val for val in order_obj.order_list if val['orderNo'] not in res]
        order_obj.save()

        return HttpResponse('')


@csrf_exempt
def get_orders(request):
    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    username = request.POST['username']
    assert_existence_of_order_model(username)

    order_obj: models.OrderModel = models.OrderModel.objects.get(username=username)

    if 'refresh' in request.POST and request.POST['refresh']:
        update_orders(order_obj, username, [val['orderNo'] for val in order_obj.order_list])

    return JsonResponse({'status': 1, 'order_list': order_obj.order_list})


@csrf_exempt
def cancel_order(request):
    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    username = request.POST['username']
    order_nums = dict(request.POST)['order_nums']
    cancel_message = models.BuyUserModel.objects.get(username=username).cancel_message

    success_list = []
    failed_list = {}
    for n in order_nums:
        ok, msg = api.cancel_order(username, n, cancel_message)

        if ok:
            success_list.append(n)
        else:
            failed_list[n] = msg

    return JsonResponse({'status': 1, 'success_list': success_list, "failed_list": failed_list})


@csrf_exempt
def get_my_delivery_info(request):
    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    username = request.POST['username']
    assert_existence_of_user(username)

    obj = models.BuyUserModel.objects.get(username=username)

    data = {
        'status': 1,
        'mail_address': obj.mail_address,
        'mail_pass': obj.mail_pass,
        'credit_card': obj.credit_card,
        'name': obj.name,
        'post_num': obj.post_num,
        'prefecture': obj.prefecture,
        'address': obj.address,
        'phone_num': obj.phone_num,
        'cancel_message': obj.cancel_message,
        'mega_wari': obj.mega_wari,
        'point': obj.point,
        'akaji': obj.akaji,
        'card_res': obj.card_res,
        'proxy': obj.proxy
    }

    return JsonResponse(data)


@csrf_exempt
def update_from_errors_to_new(request):
    username = str(request.user)

    order_obj = models.OrderModel.objects.get(username=username)
    order_list = order_obj.order_list
    failed_order_list = order_obj.failed_order_list
    try:
        if type(request.body) == bytes:
            res = json.loads(request.body)
        else:
            return JsonResponse({})
    except Exception as e:
        print(str(e))
        return JsonResponse({})

    for order_num in res.keys():
        val = res[order_num]
        for order in failed_order_list:
            if order['orderNo'] == int(order_num):
                failed_order_list.remove(order)

                order["receiver"] = val['name']
                order["receiverTel"] = val['phone_num']
                order["receiverMobile"] = val['mobile_num']
                order["shippingAddr"] = val['address']
                order["zipCode"] = val['zip_code']
                order.pop('reason')

                order_list.append(order)

                break

    order_obj.save()

    return JsonResponse({})


# INPUT: remove_from_new: [order_no, order_no, ...], add_to_failed_list: [[order_no, reason], [order_no, reason], ...]
@csrf_exempt
def edit_orders(request):
    temp = json.loads(request.body)

    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    username = temp['username']
    remove_from_new_orders = temp['remove_from_new'] if 'remove_from_new' in temp.keys() else []
    add_to_failed_list = temp['add_to_failed_list'] if 'add_to_failed_list' in temp.keys() else []

    order_obj = models.OrderModel.objects.get(username=username)
    order_list = order_obj.order_list
    failed_order_list = order_obj.failed_order_list

    failed_to_add = []
    for temp in add_to_failed_list:
        order_no = int(temp[0])
        reason = temp[1]
        elm = None
        for obj in order_list:
            if obj['orderNo'] == order_no:
                elm = obj

        if elm:
            elm['reason'] = reason
            failed_order_list.append(elm)
            remove_from_new_orders.append(order_no)
        else:
            failed_to_add.append(order_no)

    failed_to_remove = []
    print(remove_from_new_orders)
    for order_no in remove_from_new_orders:
        removed = False
        for order in order_list:
            if order['orderNo'] == int(order_no):
                order_list.remove(order)
                removed = True
                break

        if not removed:
            failed_to_remove.append(order_no)

    order_obj.save()

    return JsonResponse({'status': 1, "failed_to_add": failed_to_add, "failed_to_remove": failed_to_remove})


# 赤字、カード残額、手数料
@csrf_exempt
def get_user_base_info(request):
    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    username = request.POST['username']
    user_obj = models.BuyUserModel.objects.get(username=username)

    user_dict = BuyUserSerializer(user_obj).data

    user_dict['status'] = 1

    user_obj = UserModel.objects.get(username=username)

    user_dict['kotei'] = {
        'min_1': user_obj.min_1,
        'max_1': user_obj.max_1,
        'max_2': user_obj.max_2,
        'max_3': user_obj.max_3,
        'max_4': user_obj.max_4,
        'kotei_1': user_obj.kotei_1,
        'kotei_2': user_obj.kotei_2,
        'kotei_3': user_obj.kotei_3,
        'kotei_4': user_obj.kotei_4,
    }

    return JsonResponse(user_dict)


@csrf_exempt
def set_sales(request):
    temp = json.loads(request.body)

    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    user_obj = User.objects.get(username=temp['username'])
    if not models.SalesModel.objects.filter(user=user_obj).exists():
        models.SalesModel(user=user_obj).save()

    if not models.AsinSalesModel.objects.filter(user=user_obj).exists():
        models.AsinSalesModel(user=user_obj).save()

    asin_sales_obj = models.AsinSalesModel.objects.get(user=user_obj)

    assert_sales_model(username=user_obj.username)
    sales_obj = models.SalesModel.objects.get(user=user_obj)

    sales_obj.singlesalemodel_set.create(
        order_num=temp['order_num'],
        order_date=temp['order_date'],
        product_name=temp['product_name'],
        qty=temp['qty'],
        name=temp['name'],
        phone_num=temp['phone_num'],
        mobile_num=temp['mobile_num'],
        address=temp['address'],
        post_code=temp['post_code'],
        q10_price=temp['q10_price'],
        user_code=temp['user_code'],
        price=temp['price'],
        point=temp['point'],
        purchase_fee=temp['purchase_fee'],
        amazon_order_num=temp['amazon_order_num'],
        kotei=temp['kotei'],
        profit=temp['profit'],
        discount=temp['discount'],
        date=datetime.datetime.now()
    )

    asin_sales_obj.add_asin(f'B{temp["user_code"][1:]}')

    sales_obj.total_profit += temp['profit']

    sales_obj.save()

    return JsonResponse({'status': 1})


@csrf_exempt
def get_sales(request):
    user_obj = User.objects.get(username=request.user)
    assert_sales_model(str(request.user))
    sales_obj = models.SalesModel.objects.get(user=user_obj)

    if type(request.body) == bytes:
        temp = json.loads(request.body)['data']
    else:
        temp = request.body['data']

    objects = sales_obj.singlesalemodel_set.filter(date__year=temp['year'], date__month=temp['month'])

    return_json = {
        "total_profit": sales_obj.total_profit
    }
    serializer = SingleSaleSerializer(objects, many=True)
    if serializer.data:
        for val in serializer.data:
            order_num = val.pop('order_num')
            return_json[order_num] = val

    return JsonResponse(return_json)


@csrf_exempt
def get_date_range(request):
    assert_sales_model(str(request.user))
    sales_obj = models.SalesModel.objects.get(user=User.objects.get(username=request.user))

    objects = sales_obj.singlesalemodel_set.all().order_by('date')

    if not objects:
        return JsonResponse({})

    return JsonResponse({
        "start": {
            'year': objects[0].date.year,
            'month': objects[0].date.month
        },
        "end": {
            'year': objects.reverse()[0].date.year,
            'month': objects.reverse()[0].date.month
        }
    })


@csrf_exempt
def delete_all_sales(request):
    user_obj = User.objects.get(username=request.user)
    assert_sales_model(str(request.user))
    sales_obj = models.SalesModel.objects.get(user=user_obj)

    sales_obj.singlesalemodel_set.all().delete()
    sales_obj.total_profit = 0

    sales_obj.save()

    asin_obj = models.AsinSalesModel.objects.get(user=user_obj)
    asin_obj.sales_list = {}
    asin_obj.save()

    return JsonResponse({})


@csrf_exempt
def send_order(request):
    temp = json.loads(request.body)

    if not assert_user_pass(request):
        return JsonResponse({'status': 0})

    res = api.send_order(temp['username'], temp['order_num'])

    print(res)

    return JsonResponse({})


@csrf_exempt
def from_error_to_profit(request):
    temp = json.loads(request.body)

    user_obj = User.objects.get(username=temp['username'])
    if not models.SalesModel.objects.filter(user=user_obj).exists():
        models.SalesModel(user=user_obj).save()

    if not models.AsinSalesModel.objects.filter(user=user_obj).exists():
        models.AsinSalesModel(user=user_obj).save()

    order_obj = models.OrderModel.objects.get(username=temp['username'])
    asin_sales_obj = models.AsinSalesModel.objects.get(user=user_obj)
    mega_wari = models.BuyUserModel.objects.get(username=temp['username']).mega_wari
    assert_sales_model(username=user_obj.username)
    sales_obj = models.SalesModel.objects.get(user=user_obj)
    obj = list_price_revision.models.UserModel.objects.get(username=temp['username'])

    ok_list = []
    for order_num in temp['li'].keys():
        try:
            order_num = int(order_num)
        except:
            continue

        for failed_order in order_obj.failed_order_list:
            if order_num == failed_order['orderNo'] and temp['li'][str(order_num)]['bought_price']:
                ok_list.append([temp['li'][str(order_num)], failed_order])
                break

    to_remove_list = []
    for val in ok_list:
        asin = 'B' + val[1]['sellerItemCode'][1:]
        price = val[0]['bought_price']

        if obj.min_1 <= price <= obj.max_1:
            kotei = obj.kotei_1
        elif price <= obj.max_2:
            kotei = obj.kotei_2
        elif price <= obj.max_3:
            kotei = obj.kotei_3
        else:
            kotei = obj.kotei_4

        if mega_wari:
            discount = val[1]['discount'] / 2
        else:
            discount = 0

        sales_obj.singlesalemodel_set.create(
            order_num=val[1]['orderNo'],
            order_date=val[1]['orderDate'],
            product_name=val[1]['itemTitle'],
            qty=val[1]['orderQty'],
            name=val[1]['receiver'],
            phone_num=val[1]['receiverTel'],
            mobile_num=val[1]['receiverMobile'],
            address=val[1]['shippingAddr'],
            post_code=val[1]['zipCode'],
            q10_price=val[1]['total'],
            user_code=val[1]['sellerItemCode'],
            price=price,
            point=0,
            purchase_fee=price,
            amazon_order_num=val[0]['amazon_order_num'],
            kotei=kotei,
            profit=val[1]['total'] - price - kotei - discount,
            discount=discount,
            date=datetime.datetime.now()
        )

        asin_sales_obj.add_asin(asin)

        sales_obj.total_profit += val[1]['total'] - price - kotei - discount

        sales_obj.save()

        to_remove_list.append(val[1])

    order_obj.failed_order_list = [val for val in order_obj.failed_order_list if val not in to_remove_list]
    order_obj.save()

    return JsonResponse({})


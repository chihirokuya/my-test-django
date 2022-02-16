import json
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from . import models
from list_price_revision.models import UserModel
from list_price_revision.views import chunked
from list_price_revision import api
from django.contrib import messages


base_path = 'autobuy/'


def assert_existence_of_user(username):
    if not models.BuyUserModel.objects.filter(username=username).exists():
        models.BuyUserModel(username=username).save()


def order_view(request):
    try:
        user_obj = UserModel.objects.get(username=request.user)
    except:
        user_obj = None

    context = {
        "obj": user_obj
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
            buy_obj.akaji = int(res['akaji'])
            buy_obj.card_res = int(res['card_res'])
            buy_obj.commission_fee = int(res['commission_fee'])
            proxy_list = []
            for proxy in res['proxy_list']:
                proxy_list.append({
                    "ip": proxy[0],
                    "port": proxy[1],
                    "id": proxy[2],
                    "password": proxy[3],
                })

            buy_obj.proxy_list = proxy_list
            buy_obj.save()

            return JsonResponse({'ok': True})
        except Exception as e:
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



# 軽API
def assert_user_pass(username, password):
    return


def order_page_api(request, mode):
    if request.method == 'GET' and 'username' in request.GET:
        username = request.GET['username']
    else:
        if request.method == 'POST' and 'username' in request.POST:
            username = request.POST['username']
        else:
            username = request.user

    if not models.OrderModel.objects.filter(username=request.user).exists():
        models.OrderModel(username=request.user, order_list=[]).save()

    order_obj: models.OrderModel = models.OrderModel.objects.get(username=username)

    order_list = {}

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

        if mode == 0:
            return JsonResponse({"order_list": order_list})
        else:
            order_number_list = list(order_list.keys())

            res = api.get_new_orders(str(username))
            key_list = []
            for val in res:
                key_list.append(val['orderNo'])
                if val['orderNo'] not in order_number_list:
                    order_obj.order_list.append(val)

            order_obj.order_list = [val for val in order_obj.order_list if val['orderNo'] in key_list]
            order_obj.save()

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


def get_orders(request):
    return JsonResponse({"data": 'test'})


def update_orders(request):
    return


def delete_orders(request):
    return
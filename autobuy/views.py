import json

from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from . import models
from list_price_revision.models import UserModel
from list_price_revision.views import chunked
from list_price_revision import api


base_path = 'autobuy/'


def order_view(request):
    try:
        user_obj = UserModel.objects.get(username=request.user)
    except:
        user_obj = None

    context = {
        "obj": user_obj
    }
    return render(request, base_path + 'order_page.html', context)



# 軽API
def order_page_api(request, mode):
    if request.method == 'GET' and 'username' in request.GET:
        username = request.GET['username']
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
            for val in res:
                if val['orderNo'] not in order_number_list:
                    order_obj.order_list.append(val)
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
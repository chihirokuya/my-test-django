from sp_api.api import Catalog, Products
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiRequestThrottledException, SellingApiBadRequestException, \
    SellingApiForbiddenException, SellingApiServerException, SellingApiTemporarilyUnavailableException
from .models import AsinModel, Q10BrandCode, UserModel, Q10ItemsLink, ListingModel, LogModel
import keepa
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from mysite.settings import MEDIA_ROOT
import csv
import re
import datetime
from .views import delimiter


# 価格設定
def to_user_price(obj: UserModel, price):
    price = int(price)

    if price <= obj.max_1:
        rieki = obj.rieki_1
        kotei = obj.kotei_1
    elif price <= obj.max_2:
        rieki = obj.rieki_2
        kotei = obj.kotei_2
    elif price <= obj.max_3:
        rieki = obj.rieki_3
        kotei = obj.kotei_3
    else:
        rieki = obj.rieki_4
        kotei = obj.kotei_4

    return int(price * (1 + rieki / 100) + kotei)


class SpApiFunction:
    credentials = None
    counter = 0

    def __init__(self):
        refresh_token_list = [
            'Atzr|IwEBIAhK-f7HQLwhjTMUw5dzX2m7d_V-LA7UspYYxk07cQYs_PAN0kr6lalMJryfpbDm7QmcoiJqgn-IyqwkssxyxkRYKPjKriRALuxVm_Ieu-rxhx8-s2MqqEOfXfO51fk9f5eqOQM2frF4FuLfpc5Qjsdrjb9XX1kkcpZSDwYqfp9DFmWCRTzxQs-1UCryRgluJRl1N5yLPyTtl0nVGLk-5rOYiayH0RvMSs5ihy5YeBDVsHOwGmwkTl0h4IYCOI_jRQjI4K4qwhv860HpMLQ96PaNLXoAXysfKLhX0boBhvQ--4Vxy-WYv2VsJFo2itxfPgU',
        ]
        lwa_app_id = "amzn1.application-oa2-client.8615bda7d6e346e48332aa5f892c3afe"
        lwa_client_secret = "07f880c663c5b4d46cdca2da0d008daabe45a66eb9278e64dd77e7bbb52ac64b"
        aws_secret_key = "5aFD+AlaAzRAOO+BMb9J7PymhWBCYzsdLn+mIJZC"
        aws_access_key = "AKIAWHNGOB2LY7VXBVED"
        role_arn = "arn:aws:iam::428235165335:role/Q_SP_ROLE"

        self.credentials = dict(
            refresh_token=random.choice(refresh_token_list),
            lwa_app_id=lwa_app_id,
            lwa_client_secret=lwa_client_secret,
            aws_secret_key=aws_secret_key,
            aws_access_key=aws_access_key,
            role_arn=role_arn
        )

    def get_offers(self, asin):
        try:
            of = Products(credentials=self.credentials, marketplace=Marketplaces.JP) \
                .get_item_offers(asin, ItemCondition="New")
            self.counter = 0
        except (SellingApiRequestThrottledException, SellingApiForbiddenException):
            self.counter += 1
            if self.counter == 10:
                return None
            time.sleep(5)
            return self.get_offers(asin)
        except (SellingApiBadRequestException, SellingApiServerException, SellingApiTemporarilyUnavailableException):
            time.sleep(3)
            return None
        except:
            return None

        return of

    def get_catalog(self, asin):
        try:
            cat = Catalog(credentials=self.credentials, marketplace=Marketplaces.JP) \
                .get_item(asin)
            self.counter = 0
        except (SellingApiRequestThrottledException, SellingApiForbiddenException):
            self.counter += 1
            if self.counter == 10:
                return None
            time.sleep(5)
            return self.get_catalog(asin)
        except (SellingApiBadRequestException, SellingApiServerException, SellingApiTemporarilyUnavailableException):
            time.sleep(3)
            return None
        except:
            return None

        return cat

    def get_lowest_price(self, offers):
        try:
            offers = offers['Offers']
        except:
            return ''

        if not offers:
            return ''

        now_price = 10000000
        updated = False

        for offer in offers:
            offer: dict
            # check FBA
            try:
                fba = offer['IsFulfilledByAmazon']
            except KeyError:
                continue

            if fba:
                try:
                    price = offer['ListingPrice']['Amount']
                except KeyError:
                    continue

                try:
                    points = offer['Points']['PointsNumber']
                except KeyError:
                    points = 0

                total_price = price - points

                if total_price < now_price:
                    now_price = total_price
                    updated = True

        if not updated:
            return ''
        else:
            return f'{int(now_price)}'

    # return product_name, brand, product_group, image_link
    def get_from_catalog(self, catalog):
        try:
            product_name = catalog['AttributeSets'][0]['Title']
        except Exception as e:
            return False, '商品名が取得できませんでした'

        try:
            brand = catalog['AttributeSets'][0]['Brand']
        except Exception as e:
            brand = ''

        product_name = product_name.replace(brand, '')

        try:
            product_group = catalog['AttributeSets'][0]['ProductGroup']
        except Exception as e:
            product_group = ''

        return True, [product_name, brand, product_group]


# return [商品名, 価格, ブランド, Amazonグループ]　または　空
def get_from_sp_api(asin):
    result = []

    sp_api = SpApiFunction()

    offers = sp_api.get_offers(asin)
    catalog = sp_api.get_catalog(asin)

    if offers is None or catalog is None:
        return result, '存在しないASIN'

    if offers.errors is not None or catalog.errors is not None:
        return result, '存在しないASIN'

    price = sp_api.get_lowest_price(offers.payload)

    if price == '':
        return result, '価格取得失敗'

    ok, values = sp_api.get_from_catalog(catalog.payload)

    if not ok or values[0] == '':
        return result, 'Keepaから情報取得失敗'

    return [values[0], int(float(price)), values[1], values[2]], ''


def keepa_info(product):
    result = []
    try:
        try:
            images = product['imagesCSV'].split(',')
        except AttributeError:
            images = []
        links = []
        for image in images:
            links.append(
                'https://images-na.ssl-images-amazon.com/images/I/' + image.replace('.jpg', '.jpg'))
    except:
        return result, '画像取得失敗'

    try:
        description = product['features']
        if description is None:
            description = []
    except:
        description = []

    try:
        jan = product['eanList'][0]
    except:
        jan = ''

    try:
        category_tree = product['categoryTree']
        if category_tree is None:
            category_tree = []
    except:
        category_tree = []

    return [links, description, jan, category_tree], ''


def get_category_qoo10(product_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X'
                             ' 10_11_5) AppleWebKit/537.36 (KHTML, like '
                             'Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    soup = BeautifulSoup(
        requests.get('https://www.qoo10.jp/s/?keyword=' + quote(product_name),
                     headers=headers).text,
        'html.parser')

    elm = soup.find(id='category_result_list')

    if elm is None:
        soup = BeautifulSoup(
            requests.get('https://www.qoo10.jp/s/?keyword=' + quote(product_name[:50]),
                         headers=headers).text,
            'html.parser')

        elm = soup.find(id='category_result_list')

        if elm is None:
            return ''

    elms = elm.find_all('a')

    if len(elms) > 0:
        for elm in elms:
            if elm.has_attr('href'):
                link = elm['href'].split('gdlc_cd=')
                if len(link) != 1:
                    if link[1][0] == '3':
                        return link[1]

    elms = soup.find_all(class_='sbj')

    if len(elms) > 0:
        link = ''
        for elm in elms:
            a_s = elm.find_all('a')

            for a in a_s:
                if a.has_attr('data-type') and a['data-type'] == 'goods_url':
                    link = a['href']
                    break

            if link != '':
                break

        if link != '':
            soup = BeautifulSoup(requests.get(link, headers).text, 'html.parser')

            elm = soup.find(id='img_search_gdsc_cd')

            if elm is not None:
                return elm['value']

    return ''


def get_cat_from_csv(category_tree):
    with open(MEDIA_ROOT + '/categories.csv', 'r', encoding='utf-8_sig',
              errors='ignore') as f:
        categories = [r for r in csv.reader(f) if r and r[0] != '']

    def match_():
        match_sec = ''
        for cat in categories:
            # if matches exactly
            if cat[5] == keyword:
                return cat[4]

            if keyword in cat[5]:
                return cat[4]

            if keyword == cat[3]:
                match_sec = cat[2]

        if match_sec != '':
            li = [cat for cat in categories if cat[3] == match_sec]
            for cat in li:
                if cat[5] == 'その他':
                    return cat[4]

        return ''

    for i in reversed(category_tree):
        try:
            keyword = i['name']
        except:
            pass

        category_num = match_()

        if category_num != '':
            return category_num

        if '・' in i['name']:
            keywords = i['name'].split('・')
            for key in keywords:
                keyword = key
                category_num = match_()
                if category_num != '':
                    return category_num

    return ''


def get_info_from_amazon(username, to_search_class, asin_list, certification_key):
    # まずSP-APIから取得できるか確認→取得できたもののみKeepaからも取得

    print('####### Amazonから取得 #########')
    # SP-APIから成功したリスト、[ [asin, [商品名, 価格, ブランド, Amazonグループ]] ]
    for asin in asin_list:
        if AsinModel.objects.filter(asin=asin).exists():
            continue

        result, message = get_from_sp_api(asin)

        # 成功したら
        if result:
            # ブランドがあるなら変換する
            if result[2]:
                if Q10BrandCode.objects.filter(brand_name=result[2]).exists():
                    code = Q10BrandCode.objects.get(brand_name=result[2]).code
                else:
                    code = search_brand(certification_key, result[2])

                    if code != '':
                        Q10BrandCode(brand_name=result[2], code=code).save()

                result[2] = code

            to_search_class.result_list[asin] = {
                "name": result[0],
                "price": result[1],
                "brand": result[2],
                "group": result[3]
            }
        # 何らかの理由でエラーが出た場合
        else:
            to_search_class.to_delete_asin_list.append(asin)
            to_search_class.log_error_reason.append([asin, message])

    # 成功したASINリスト
    succeed_asin_list = [asin for asin in list(to_search_class.result_list.keys()) if
                         not AsinModel.objects.filter(asin=asin).exists()]
    # ASINを10個ずつに分ける
    temp = []
    for i in range(0, len(succeed_asin_list), 10):
        temp.append(succeed_asin_list[i:i + 10])

    keepa_key = 'e4s4q8m7evnnrdsn095aj3llhbcmsqa13v0f5igam6vnomlplb970pduatfrdbi9'
    api = keepa.Keepa(keepa_key)

    for asins in temp:
        try:
            products = api.query(asins, wait=True, domain='JP')
        except Exception as e:
            for asin in asins:
                to_search_class.to_delete_asin_list.append(asin)
                to_search_class.log_error_list.append([asin, str(e)])
            continue

        for product in products:
            result, message = keepa_info(product)

            if result:
                category = get_category_qoo10(to_search_class.result_list[product['asin']]['name'])

                print('category1', category)

                if category == '':
                    category = get_cat_from_csv(result[3])
                    print('category2', category)

                to_search_class.result_list[product['asin']]['links'] = result[0]
                to_search_class.result_list[product['asin']]['description'] = result[1]
                to_search_class.result_list[product['asin']]['jan'] = result[2]
                to_search_class.result_list[product['asin']]['category_tree'] = result[3]
                to_search_class.result_list[product['asin']]['q10_category'] = category
            else:
                to_search_class.to_delete_asin_list.append(product['asin'])
                to_search_class.log_error_list.append([product['asin'], message])

    print('ASIN取得完了')





# qoo10系
def get_api_key(username):
    return UserModel.objects.get(username=username).q10_api


# return Certification_key or None
def get_certification_key(username):
    try:
        api_key = get_api_key(username)

        user_id = UserModel.objects.get(username=username).q10_id
        password = UserModel.objects.get(username=username).q10_password
        res = requests.get(
            'http://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi?'
            f'key={api_key}'
            '&v=1.0'
            '&returnType=json&method=CertificationAPI.CreateCertificationKey&'
            f'user_id={user_id}'
            f'&pwd={password}'
        ).json()

        return res['ResultObject']
    except:
        return ''


# ['SellerCode']
def get_all_items(certification_key):
    res = requests.get(
        f'http://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi'
        f'?key={certification_key}'
        '&v=1.0'
        '&returnType=json'
        '&method=ItemsLookup.GetAllGoodsInf'
        'o&ItemStatus=S2'
        '&Page=1').json()

    total_page = res['ResultObject']['TotalPages']
    total_items = res['ResultObject']['TotalItems']

    if total_items == 0:
        return []

    items = res['ResultObject']['Items']

    for page in range(2, total_page + 1):
        res = requests.get(
            f'http://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi'
            f'?key={certification_key}'
            '&v=1.0'
            '&returnType=json'
            '&method=ItemsLookup.GetAllGoodsInf'
            'o&ItemStatus=S2'
            '&Page=1').json()

        items.extend(res['ResultObject']['Items'])

    items = [val['SellerCode'] for val in items]

    return items


def search_brand(certification_key, keyword):
    res = requests.get(
        f'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0&method=CommonInfoLookup.SearchBran'
        f'd&key={certification_key}&keyword={keyword}').json()['ResultObject']

    print(res)
    brand_code = ''
    if res:
        brand_code = re.sub('\\D', '', res[0]['M_B_NO'])

    return brand_code


def upload_new_item(asin, username, certification_key):
    user_obj = UserModel.objects.get(username=username)
    initial_letter = user_obj.initial_letter
    stock_num = user_obj.stock_num
    shipping_code = user_obj.shipping_code

    # ブラックリスト系
    try:
        black_maker_item_name = user_obj.maker_name_blacklist.split('\n')
        black_asins = user_obj.asin_blacklist.split('\n')
        remove_words = user_obj.words_blacklist.split('\n')
        black_amazon_group = user_obj.group_black.split(',')
    except:
        black_maker_item_name = []
        black_asins = []
        remove_words = []
        black_amazon_group = []

    print('itemname', black_maker_item_name)

    black = False
    print('ブラック')
    print(black_asins)
    print('ASIN')
    print(asin)
    for black_asin in black_asins:
        if asin == black_asin:
            black = True
            break
    if black:
        return False, 'ASINブラックリストに含まれています。'

    try:
        obj = AsinModel.objects.get(asin=asin)
    except:
        return False, '登録されていないASINです。'

    try:
        if obj.product_group and obj.product_group in black_amazon_group:
            return False, '商品グループがブラックリストに含まれています。'
    except:
        pass

    for black_word in black_maker_item_name:
        if black_word in obj.description.split('\n') or black_word == obj.product_name:
            black = True
            break
    if black:
        return False, '商品名またはメーカ名にブラックリストキーワードが入っています。'

    to_remove_list = []
    product_name = obj.product_name
    description = obj.description.split('\n')
    for remove_word in remove_words:
        product_name = product_name.replace(remove_word, '')
        for desc in description:
            if remove_word in desc:
                to_remove_list.append(desc)

    for desc in to_remove_list:
        if desc in description:
            description.remove(desc)

    images = obj.photo_list.split('\n')

    header = {
        "Content-Type": 'application/x-www-form-urlencoded',
        "QAPIVersion": '1.1',
        'GiosisCertificationKey': certification_key
    }

    html = '<div>'
    for val in description:
        html += f'<li>{val}</li>'
    html += '</div>'

    data = {
        'SecondSubCat': obj.q10_category,
        'OuterSecondSubCat': '',
        'Drugtype': '',
        'BrandNo': str(obj.brand),
        'ItemTitle': product_name,
        'PromotionName': '',
        'SellerCode': initial_letter + obj.asin[1:],
        'IndustrialCodeType': 'J' if obj.jan else '',
        'IndustrialCode': obj.jan,
        'ModelNM': '',
        'ManufactureDate': '',
        'ProductionPlaceType': '',
        'ProductionPlace': '',
        'Weight': '',
        'Material': '',
        'AdultYN': 'N',
        'ContactInfo': '',
        'StandardImage': images[0],
        'VideoURL': '',
        'ItemDescription': html,
        'AdditionalOption': '',
        'ItemType': '',
        'RetailPrice': 0,
        'ItemPrice': float(to_user_price(user_obj, int(float(obj.price)))),
        'ItemQty': int(stock_num),
        'ShippingNo': int(shipping_code),
        'AvailableDateType': '3',
        'AvailableDateValue': '20:00',
        'Keyword': obj.product_name[:30]
    }

    res = requests.post('https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsBasic.SetNewGoods',
                        headers=header, data=data).json()

    print(res)

    if res['ResultCode'] == 0:
        if images[1:]:
            link = 'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsContents.EditGoodsMultiImage'

            data = {"SellerCode": initial_letter + obj.asin[1:]}

            photo_num = user_obj.photo_num
            for i, val in enumerate(images[1:]):
                if i == photo_num:
                    break
                data[f'EnlargedImage{i + 1}'] = val

            res = requests.post(link, headers=header, data=data)

            print(res.json())

        return True, ''
    else:
        try:
            if 'Can not register the goods' in res['ResultMsg']:
                return True, res['ResultMsg']
        except:
            pass

        return False, '出品失敗'


# [product_name, brand, description, jan, q10_category, price]
def get_item_info(certification_key, seller_code):
    link = f'https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.1&method=ItemsLookup.GetItemDetailInfo&key={certification_key}&SellerCode={seller_code}'

    res = requests.get(link).json()

    if 'ResultObject' in res.keys():
        res = res['ResultObject'][0]
    else:
        return []

    product_name = res['ItemTitle']
    brand = res['BrandNo']

    description = res['ItemDetail'].replace('<div>', '').replace('<li>', '').replace('</div>', '').replace('</li>',
                                                                                                           '\n')
    jan = res['IndustrialCode']
    q10_category = res['SecondSubCatCd']
    price = res['ItemPrice']

    return [product_name, brand, description, jan, q10_category, price]


def link_q10_items(certification_key, username):
    item_link_obj: Q10ItemsLink = Q10ItemsLink.objects.get(username=username)
    if item_link_obj.still_getting:
        return
    else:
        item_link_obj.still_getting = True
        item_link_obj.save()

    if not ListingModel.objects.filter(username=username).exists():
        ListingModel(username=username).save()
    listing_obj: ListingModel = ListingModel.objects.get(username=username)

    listing_obj.asin_list = ''
    listing_obj.save()

    items = get_all_items(certification_key)

    keepa_key = 'e4s4q8m7evnnrdsn095aj3llhbcmsqa13v0f5igam6vnomlplb970pduatfrdbi9'
    api = keepa.Keepa(keepa_key)

    item_link_obj.total_asin_list = ','.join(items)
    item_link_obj.linked_asin_list = ''
    item_link_obj.save()

    # max length: 10
    temp_list = []

    def update_to_finished(code):
        temp: list = item_link_obj.linked_asin_list.split(',')
        temp.append(code)
        item_link_obj.linked_asin_list = ','.join(temp)
        item_link_obj.save()

        return True

    def keepa_fun(asin_list: list):
        # 3回ためす
        for j in range(3):
            try:
                products = api.query([val[0] for val in asin_list], wait=True, domain='JP')
            except:
                if j == 2:
                    print('LinkQ10: Keepaに３回以内に接続できませんでした。')
                    break
                time.sleep(3)
                continue

            to_delete_list = []
            for i, product in enumerate(products):
                try:
                    product_group = product['productGroup']
                except:
                    print('failed on product group')
                    to_delete_list.append(asin_list[i])
                    continue

                photo_list = []
                try:
                    images = product['imagesCSV'].split(',')
                except AttributeError:
                    print('failed image', asin_list[i][0])
                    to_delete_list.append(asin_list[i])
                    continue

                if not images:
                    to_delete_list.append(asin_list[i])
                    continue

                for image in images:
                    photo_list.append(
                        'https://images-na.ssl-images-amazon.com/images/I/' + image.replace('.jpg', '.jpg'))

                try:
                    category_tree = product['categoryTree']
                    if category_tree is None:
                        to_delete_list.append(asin_list[i])
                        continue
                except:
                    print('failed on cat')
                    to_delete_list.append(asin_list[i])
                    continue

                asin_list[i].append([product_group, photo_list, category_tree])

            for li in to_delete_list:
                asin_list.remove(li)

            break

        return asin_list

    def update_listing(asin_):
        # AsinListに追加
        temp = listing_obj.asin_list.split(',')
        temp.append(asin_)
        listing_obj.asin_list = ','.join(temp)
        listing_obj.save()

    for asin in items:
        if AsinModel.objects.filter(asin='B' + asin[1:]).exists():
            update_listing('B' + asin[1:])
        elif len(asin) == 10:
            result_list = get_item_info(certification_key, asin)

            if result_list:
                temp_list.append(['B' + asin[1:], result_list])

        update_to_finished(asin)

        # 10個溜まったならKeepaで取得
        if len(temp_list) == 10:
            res = keepa_fun(temp_list)

            for result in res:
                try:
                    # result: [asin, [product_name, brand, description, jan, q10_category, price], [product_group, photo_list, category_tree]]
                    obj = AsinModel()
                    obj.asin = result[0]
                    obj.product_name = result[1][0]
                    obj.brand = result[1][1]
                    obj.description = result[1][2]
                    obj.jan = result[1][3]
                    obj.q10_category = result[1][4]
                    obj.price = int(float(result[1][5]))
                    obj.product_group = result[2][0]
                    obj.photo_list = '\n'.join(result[2][1])
                    obj.category_tree = result[2][2]
                    obj.save()

                    update_listing(result[0])
                except Exception as e:
                    print('LinkQ10Items: リンクに失敗', str(e))

            temp_list = []

    item_link_obj.still_getting = False
    item_link_obj.save()


def delete_item(certification_key, item_code):
    try:
        header = {
            "Content-Type": 'application/x-www-form-urlencoded',
            "QAPIVersion": '1.1',
            'GiosisCertificationKey': certification_key
        }

        res = requests.get(
            'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0&returnType=&method=ItemsBasic.EditGoodsStatus'
            f'&key={certification_key}&SellerCode={item_code}&Status=3', headers=header
        ).json()

        if res['ResultCode'] == 0:
            return True
        else:
            if 'Fail to find Item' in res['ResultMsg']:
                return True
            return [False, res['ResultMsg']]
    except Exception as e:
        return [False, str(e)]


def update_price(username):
    certification_key = get_certification_key(username)

    log_success = []
    log_failed = []
    log_total = []

    def add_log(ok, key, reason=''):
        log_total.append(key)
        if ok:
            log_success.append(key)
        else:
            log_failed.append([key, reason])

            delete_item(certification_key, initial_letter + asin[1:])

    try:
        user_obj: UserModel = UserModel.objects.get(username=username)
        initial_letter = user_obj.initial_letter
    except:
        return

    listing_obj: ListingModel = ListingModel.objects.get(username=username)
    asin_list = listing_obj.asin_list.split(',')

    for asin in asin_list:
        try:
            try:
                asin_obj: AsinModel = AsinModel.objects.get(asin=asin)
            except:
                add_log(False, asin, '存在しないASIN')
                continue

            link = 'https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0' \
                   f'&method=ItemsOrder.SetGoodsPriceQty&key={certification_key}&SellerCode={initial_letter + asin[1:]}' \
                   f'&Price={to_user_price(user_obj, asin_obj.price)}&Qty={user_obj.stock_num}'

            res = requests.get(link).json()

            if 'ResultCode' in res.keys() and res['ResultCode'] == 0:
                add_log(True, asin)
            else:
                error_message = '不明'
                if 'ResultMsg' in res.keys():
                    error_message = res['ResultMsg']
                elif 'ResultCode' in res.keys():
                    code = res['ResultCode']
                    error_message = ''
                    if code == -10000:
                        error_message = '販売者認証キーを確認してください。'
                    elif code == -10001:
                        error_message = "'ItemCode', 'SellerCode' の商品情報が見つかりません。"
                    elif code == -10101:
                        error_message = '処理エラー - [エラーメッセージ]'
                    elif code == -90001:
                        error_message = 'APIが存在しません'
                    elif code in [-90004, -90005]:
                        error_message = '販売者認証キーが期限切れです。新しいキーを使用してください。'

                add_log(False, asin, error_message)
        except Exception as e:
            add_log(False, asin, str(e))

    temp = [val[0] for val in log_failed]
    log_total_list = temp
    log_total_list.extend(log_success)
    cause_list = ''
    for val in log_failed:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    LogModel(username=username, type='価格改定', input_asin_list=','.join(log_total_list),
             success_asin_list=','.join(log_success), cause_list=cause_list,
             date=datetime.datetime.now()).save()


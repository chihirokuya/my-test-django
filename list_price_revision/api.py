import threading
from sp_api.api import Catalog, Products
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiRequestThrottledException, SellingApiBadRequestException, \
    SellingApiForbiddenException, SellingApiServerException, SellingApiTemporarilyUnavailableException
from .models import AsinModel, Q10BrandCode, UserModel, Q10ItemsLink, ListingModel, LogModel, RecordsModel
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
import unicodedata
import emoji

refresh_token_list = [
    'Atzr|IwEBIAhK-f7HQLwhjTMUw5dzX2m7d_V-LA7UspYYxk07cQYs_PAN0kr6lalMJryfpbDm7QmcoiJqgn-IyqwkssxyxkRYKPjKriRALuxVm_Ieu-rxhx8-s2MqqEOfXfO51fk9f5eqOQM2frF4FuLfpc5Qjsdrjb9XX1kkcpZSDwYqfp9DFmWCRTzxQs-1UCryRgluJRl1N5yLPyTtl0nVGLk-5rOYiayH0RvMSs5ihy5YeBDVsHOwGmwkTl0h4IYCOI_jRQjI4K4qwhv860HpMLQ96PaNLXoAXysfKLhX0boBhvQ--4Vxy-WYv2VsJFo2itxfPgU',
    'Atzr|IwEBIBMy28_I_H04XEQhGuwRv-ChgFeybLouZ-oVZ7S9d1wIMtz2pfc_prOF8pU60ZkitfsysDl3KfSG-TZ9OfAmdThA5LDA6Ns4gv2t621ZO5QQiROevC42uteGKRmso5f-1M7MvG1GGeHpYI4IYFbIE6_zERSHlypNueiDDurV5h-ech1cWOBpfDVA6GPzSqPNHenIHHWFPf6W56wXOLPDYqsTA15SOsm0B0Mz1MCylFWuUtVCuLqWm21wt5oM88XYXdicvJLxqOdcc8K76YXzwY3uNWLMSiaQWACKtDEKeM9SnZIkWS2DVlAAgljipQavZgY',
    'Atzr|IwEBIKcYx0VORNNPP7uck84iHvbgVqXaqRBXaLBWSIOX6l-OsXJ3ZluTfYnMyCpfdQF2ZII7262hZUt745IwXAsoLdqmz4lXlrV5QcKlocA-qQKA9I8mXtDEwaGt3P6_yVRkYNPaPe6f4DP9dUsGxnc4SmGhgA76tdNbGG7W3j3eRRuHIRe2h-onqOHK666jGT7DJ33kG6GXXJLaUzoDFV6lEqdhna7o4Fr8N9P0nGoio540NNtoyRhCoGIdwL2Gs2cOmkX4egzPlwOpkWwP-rpIIGyuMEdBQ5xy1RmdTQrDiSuCUsCpQxo6UvOreYn6LwEj078',
    'Atzr|IwEBIEt_BdYf_R9sXGlcXMVGlD-HIFfh3IMRrAYYBjHBEfZxRmHVGJUp1XCT_8As4Is1YmjTxmiEO28CWRO_7WHv-tQafOxiSmmssL99juM1HZsNeNi4zhmc88cWLvDMGClSUd6n9qxQ2siwQNS9vPZU2FZnwkhAVv7qwKcScB0MAG9Wy1T9KGftz2aH5J754Dsk0pNTPZfoAsUS_YQh2fzrZ-t-QRIKObtGNpJtWvkkb_Lb2VwSVrCtrT5oe9pkVAk3B_TKaTtxxccfmtoPrbE7EtFF_oBwUQJLCfkaiyrdhIE2ljaB4Vme08GgXbgISaTWqwA',
    'Atzr|IwEBICzy6j0IcrIR9a1KkR9cSLQcvUWU_0ESstbuMt8qeJseIDSIIEDTZriQS0SgMY2CLuCjFQ3zQ-aNE6YCeIU1hhhzJ3hL6_GBWt7NObv9kOw501PKrifoSS6WjevLW4rtK80NJHz6VAXCCuZVt5wxu2UYgZPcLjpeTkGGhBZieswDpPIWZrlw6N6nNmEblVcI4A1baBUDTHKaAAzt-znMjH7ExYoYGzXncTpTnGAtAycum1HPuAc41NAC8Skjdz3kd8V_e6Kd9SySAtYeOslcTogawTyDEQiiEZP13so0LogB0XcNJ1Ivfj2ZZf47rlRLwG4',
    'Atzr|IwEBILp_NZHMGfdhVJ2Ox1pYZnoZ556GZJpGsCKR3YZyFuYRkAF-1xIj4wDxLdn8rMtT6SC056ICcDTcp-8yPOxhwA71KQ936cDoD64SYoiSVk-ABShD5pydGZ0xIDV86fm2g21XACnLYFAOoU5A7NQCvjP6Gs_mZczHhuvxRS7VWovFszuaeuRB6_--aWJBcwEBxoX7pP9I03qmUd6Y7guOvMlyc-zpNUPiluCD8uh3yZOuqQgdiiI3mRonRY4zTGuJx9OHyUKSENk0wu_equGwPFNildKhNDcpkpKLi9mUQONNYGqOYNppPuUYM8HgweFZqgA'
]

keepa_key_list = [
    'e4s4q8m7evnnrdsn095aj3llhbcmsqa13v0f5igam6vnomlplb970pduatfrdbi9',
    'gjvt2fh7m6t2f8hqoon1nm9sr9ud3sii96cjk93634ad52ko51ca8h6sdq5jp2c9',
    '34kqglknrdln8f7r3san1p32ll6qck0digu02fave85sm44p6nq89a832fm3g12n',
    'dmq15gijl45cpeo5taotisi8hg43e1cp9c52tuptauhp9o0re9e53de6icthd11e',
    'f4vopjo0njooe25tmei9v4ac0ie6rs43mknviamghc0konbpra5270892849hg3f',
    '9egm5oei3onau2k5ti1mpo85fovgiv3m9d5im3qrlpnkr3mh81s40tfgg5l5ioh8',
    '49hj7bckak5b66juiu9elpmm99858mdr8vef4a9sm3vf8hd83hhdjprc30mnjd1u',
    '5kpuo6212bfln4juqt83o4ilgdubo6fc06ta5u8qaolg7vrmf387g9vcb2b9lk7s',
    '4cpa03v0l1l2fau0slg9lvoqp9lcpcl09chevdn5ot3oj372pjr3hlj58e9ki1ca',
    'b26q7thu7vchm5fo2spe3f6anp7et270bs45nd4nii5dp37jqm7iuo4df0snd21i'
]


# 価格設定
def to_user_price(obj: UserModel, price):
    price = int(price)

    if obj.min_1 > price or obj.max_4 < price:
        return 0

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

    x = price * (1 + rieki / 100) + kotei

    return int(x)


# API用の価格設定
def user_price_and_profit(obj: UserModel, price):
    price = int(price)

    if obj.min_1 > price or obj.max_4 < price:
        return 0, 0

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

    x = price * (1 + rieki / 100) + kotei

    sell_price = int(x)
    profit = int(sell_price - price - kotei - sell_price * 0.1)

    return sell_price, profit


# ブラックリストに含まれるか
def is_in_black(user_obj: UserModel, asin_obj: AsinModel):
    ad_obj = UserModel.objects.get(username='admin')
    asin = asin_obj.asin

    try:
        black_maker_item_name = list(filter(None, ad_obj.maker_name_blacklist.split('\n')))
        black_asins = list(filter(None, ad_obj.asin_blacklist.split('\n')))
        remove_words = ad_obj.words_blacklist.split('\n')
        black_amazon_group = user_obj.group_black.split(',')
    except:
        black_maker_item_name = []
        black_asins = []
        remove_words = []
        black_amazon_group = []

    black = False
    asin_black = ''
    for black_asin in black_asins:
        if asin == black_asin.strip():
            asin_black = asin
            black = True
            break
    if black:
        return False, f'ASINブラックリストに含まれています。{asin}'

    try:
        if asin_obj.product_group and asin_obj.product_group in black_amazon_group:
            return False, f'商品グループがブラックリストに含まれています。'
    except:
        pass

    if asin_obj.brand:
        try:
            brand_name = Q10BrandCode.objects.filter(code=asin_obj.brand)[0].brand_name
        except Exception as e:
            print(e)
            brand_name = ''
            pass
    else:
        brand_name = ''

    black = False
    black_keyword = ''
    for black_word in black_maker_item_name:
        for desc in asin_obj.description.split('\n'):
            if black_word in desc:
                black_keyword = black_word
                black = True
        if black:
            break

        if black_word in asin_obj.product_name or black_word in brand_name:
            black_keyword = black_word
            black = True
            break
    if black:
        return False, f'商品名またはメーカ名にブラックリストキーワードが入っています。{black_keyword}'

    return True, ''


class SpApiFunction:
    credentials = None
    counter = 0

    def __init__(self):
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
            return '', '価格取得失敗'

        if not offers:
            return '', '価格取得失敗'

        now_price = 10000000
        point = 0
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
                    point = points
                    now_price = total_price
                    updated = True

        if not updated:
            return '', 'FBA商品ではありませんでした。'
        else:
            return f'{int(now_price)}', point

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
        return result, '存在しないASIN', ''

    if offers.errors is not None or catalog.errors is not None:
        return result, '存在しないASIN', ''

    price, point = sp_api.get_lowest_price(offers.payload)

    if price == '':
        return result, point, ''

    ok, values = sp_api.get_from_catalog(catalog.payload)

    if not ok or values[0] == '':
        return result, 'Keepaから情報取得失敗', ''

    return [values[0], int(float(price)), values[1], values[2]], '', point


# [links, description, jan, category_tree], '' または [], '理由'
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
                'https://images-na.ssl-images-amazon.com/images/I/' + image.replace('.jpg', '.jpg')
            )
        if not links:
            return result, '画像取得失敗'
    except:
        return result, '画像取得失敗'

    try:
        d_ = product['features']
        if d_ is None:
            d_ = []
    except:
        d_ = []

    description = []
    for d in d_:
        description.append(unicodedata.normalize('NFKC', emoji.get_emoji_regexp().sub(u'', d).strip()))

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
    # proxy_list_path = MEDIA_ROOT + '/ips-zone3.txt'
    #
    # with open(proxy_list_path, 'r') as f:
    #     temp = f.read().split('\n')
    #
    proxies = {
        "http": "http://lum-customer-c_e05e8a0c-zone-zone3:b6dy41se5fsa@zproxy.lum-superproxy.io:22225",
        "https": "https://lum-customer-c_e05e8a0c-zone-zone3:b6dy41se5fsa@zproxy.lum-superproxy.io:22225",
    }

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X'
                             ' 10_11_5) AppleWebKit/537.36 (KHTML, like '
                             'Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    soup = BeautifulSoup(
        requests.get('https://www.qoo10.jp/s/?keyword=' + quote(product_name),
                     headers=headers, proxies=proxies).text,
        'html.parser')

    elm = soup.find(id='category_result_list')

    if elm is None:
        soup = BeautifulSoup(
            requests.get('https://www.qoo10.jp/s/?keyword=' + quote(product_name[:50]),
                         headers=headers, proxies=proxies).text,
            'html.parser')

        elm = soup.find(id='category_result_list')

        if elm is None:
            print('elm none')
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
            soup = BeautifulSoup(requests.get(link, headers, proxies=proxies).text, 'html.parser')

            elm = soup.find(id='img_search_gdsc_cd')

            if elm is not None:
                print('found')
                return elm['value']

    return ''


def get_cat_from_csv(category_tree):
    print(category_tree)
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


def get_info_from_amazon(username, to_search_class, asin_list, certification_key, records_model: RecordsModel):
    # まずSP-APIから取得できるか確認→取得できたもののみKeepaからも取得

    print('####### Amazonから取得 #########')
    temp = len(asin_list) // 10
    if temp == 0:
        temp = 1
    # SP-APIから成功したリスト、[ [asin, [商品名, 価格, ブランド, Amazonグループ]] ]
    for i, asin in enumerate(asin_list):
        skip = False
        if AsinModel.objects.filter(asin=asin).exists():
            skip = True

        if not skip:
            result, message, point = get_from_sp_api(asin)

            # 成功したら
            if result:
                # ブランドがあるなら変換する
                if result[2]:
                    if Q10BrandCode.objects.filter(brand_name=result[2]).exists():
                        code = Q10BrandCode.objects.filter(brand_name=result[2])[0].code
                    else:
                        code = search_brand(certification_key, result[2])

                        if code != '':
                            Q10BrandCode(brand_name=result[2], code=code).save()

                    result[2] = code

                to_search_class.result_list[asin] = {
                    "name": result[0],
                    "price": result[1],
                    "brand": result[2],
                    "group": result[3],
                    "point": point
                }
            # 何らかの理由でエラーが出た場合
            else:
                to_search_class.to_delete_asin_list.append(asin)
                to_search_class.log_error_reason.append([asin, message])

        to_search_class.counter += 1
        if not i % temp:
            records_model.status_text = f'ステップ１　{to_search_class.counter}/{to_search_class.total_length}'
            records_model.save()

    # 成功したASINリスト
    succeed_asin_list = [asin for asin in list(to_search_class.result_list.keys()) if
                         not AsinModel.objects.filter(asin=asin).exists()]

    weight_list = []
    for key in keepa_key_list:
        try:
            temp_ = keepa.Keepa(accesskey=key)
            weight_list.append(temp_.tokens_left)
        except:
            pass

    total = sum(weight_list)
    length_list = [int(val / total * len(succeed_asin_list)) for val in weight_list]

    divided_asin_list = []  # 分けた後のasinリスト
    current_pos = 0
    for i, val in enumerate(length_list):
        if i == len(weight_list) - 1:
            divided_asin_list.append(succeed_asin_list[current_pos:])
        else:
            divided_asin_list.append(succeed_asin_list[current_pos: current_pos + val])
            current_pos += val

    class CounterClass:
        counter = 0

        def __init__(self):
            self.counter = 0

        def update_records(self):
            records_model.status_text = f'ステップ２ {to_search_class.step_2_counter}/{to_search_class.total_length}'
            records_model.save()

    def search_func(to_do_list, keepa_key, counter_class: CounterClass, update):
        # ASINを10個ずつに分ける
        temp = []
        for i in range(0, len(to_do_list), 10):
            temp.append(to_do_list[i:i + 10])

        api = keepa.Keepa(keepa_key)

        for asins in temp:
            try:
                products = api.query(asins, wait=True, domain='JP')
            except Exception as e:
                products = []
                for asin_ in asins:
                    try:
                        products.append(api.query(asin_, wait=True, domain='JP')[0])
                    except:
                        to_search_class.to_delete_asin_list.append(asin_)
                        to_search_class.log_error_reason.append([asin_, str(e)])

            for product in products:
                resul_, message_ = keepa_info(product)

                if resul_:
                    category = get_category_qoo10(to_search_class.result_list[product['asin']]['name'])

                    if category == '':
                        category = get_cat_from_csv(resul_[3])

                    if category == '':
                        to_search_class.to_delete_asin_list.append(product['asin'])
                        to_search_class.log_error_reason.append([product['asin'], 'カテゴリ取得に失敗しました。'])
                        to_search_class.result_list.pop(product['asin'])
                    else:
                        to_search_class.result_list[product['asin']]['links'] = resul_[0]
                        to_search_class.result_list[product['asin']]['description'] = resul_[1]
                        to_search_class.result_list[product['asin']]['jan'] = resul_[2]
                        to_search_class.result_list[product['asin']]['category_tree'] = resul_[3]
                        to_search_class.result_list[product['asin']]['q10_category'] = category
                else:
                    to_search_class.to_delete_asin_list.append(product['asin'])
                    to_search_class.log_error_reason.append([product['asin'], message_])
                    to_search_class.result_list.pop(product['asin'])

            to_search_class.step_2_counter += len(asins)
            if update:
                counter_class.update_records()

    thread_list = []
    max_index = weight_list.index(max(weight_list))
    c_c = CounterClass()
    for i, val in enumerate(divided_asin_list):
        if val:
            thread_list.append(
                threading.Thread(
                    target=search_func,
                    kwargs={
                        "to_do_list": val,
                        "keepa_key": keepa_key_list[i],
                        'counter_class': c_c,
                        'update': i == max_index
                    }
                )
            )
    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()

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
        header = {
            "Content-Type": 'application/x-www-form-urlencoded',
            "QAPIVersion": '1.0',
            "GiosisCertificationKey": api_key
        }

        data = {
            "user_id": user_id,
            "pwd": password,
        }

        res = requests.post(
            'http://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/CertificationAPI.CreateCertificationKey',
            data=data,
            headers=header
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
            f'&Page={page}').json()

        items.extend(res['ResultObject']['Items'])

    items = [val['SellerCode'] for val in items]

    return list(dict.fromkeys(items))


def search_brand(certification_key, keyword):
    res = requests.get(
        f'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0&method=CommonInfoLookup.SearchBran'
        f'd&key={certification_key}&keyword={keyword}').json()['ResultObject']

    brand_code = ''
    if res:
        brand_code = re.sub('\\D', '', res[0]['M_B_NO'])

    return brand_code


def set_header_footer(certification_key, item_code, header, footer):
    headers = {
        "Content-Type": 'application/x-www-form-urlencoded',
        "QAPIVersion": '1.0',
        'GiosisCertificationKey':certification_key
    }

    data = {
        'SellerCode': item_code,
        'EditHeaderYN': True,
        'Header': header,
        "EditFooterYN": True,
        "Footer": footer
    }

    url = 'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsContents.EditGoodsHeaderFooter'

    res = requests.post(url, headers=headers, data=data).json()

    if res['ResultCode'] == 0:
        return True, ''
    else:
        try:
            return False, res['ResultMsg']
        except Exception as e:
            return False, str(e)


def update_available_data_type(cert_key, item_code):
    header = {
        "Content-Type": 'application/x-www-form-urlencoded',
        "QAPIVersion": '1.1',
        'GiosisCertificationKey': cert_key
    }

    data = {
        "SellerCode": item_code
    }
    get_info_path = '/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsLookup.GetItemDetailInfo'

    try:
        res = requests.post('https://api.qoo10.jp' + get_info_path,
                            headers=header, data=data).json()['ResultObject'][0]

        data = {
            'SecondSubCat': res['SecondSubCatCd'],
            'OuterSecondSubCat': '',
            'Drugtype': '',
            'BrandNo': res['BrandNo'],
            'ItemTitle': res['ItemTitle'],
            'PromotionName': '',
            'SellerCode': item_code,
            'IndustrialCodeType': 'J' if res['IndustrialCode'] else '',
            'IndustrialCode': res['IndustrialCode'],
            'ModelNM': '',
            'ManufactureDate': '',
            'ProductionPlaceType': '3',
            'ProductionPlace': '',
            'Weight': '',
            'Material': '',
            'AdultYN': 'N',
            'ContactInfo': '',
            'StandardImage': res['ImageUrl'],
            'VideoURL': '',
            'ItemDescription': res['ItemDetail'],
            'AdditionalOption': '',
            'ItemType': '',
            'RetailPrice': 0,
            'ItemPrice': res['ItemPrice'],
            'ItemQty': res['ItemQty'],
            'ShippingNo': res['ShippingNo'],
            'AvailableDateType': '0',
            'AvailableDateValue': '1',
            'Keyword': res['Keyword']
        }

        res = requests.post('https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsBasic.UpdateGoods',
                            headers=header, data=data).json()
    except:
        return


def upload_new_item(asin, username, certification_key):
    user_obj = UserModel.objects.get(username=username)
    if not UserModel.objects.filter(username='admin').exists():
        UserModel(username='admin').save()
    ad_obj = UserModel.objects.get(username='admin')
    initial_letter = user_obj.initial_letter
    stock_num = user_obj.stock_num
    shipping_code = user_obj.shipping_code

    # header and footer
    def to_html(text):
        text = text.split('\n')

        save_text = '<div style="text-align:left">'

        for i in range(len(text)):
            if text[i] == '':
                continue

            save_text += text[i] + '<br><br>'

        save_text += '</div>'
        return save_text

    desc_header = to_html(user_obj.description_header)
    desc_footer = to_html(user_obj.description_footer)

    # ブラックリスト系
    try:
        black_maker_item_name = list(filter(None, ad_obj.maker_name_blacklist.split('\n')))
        black_asins = list(filter(None, ad_obj.asin_blacklist.split('\n')))
        remove_words = ad_obj.words_blacklist.split('\n')
        black_amazon_group = user_obj.group_black.split(',')
    except:
        black_maker_item_name = []
        black_asins = []
        remove_words = []
        black_amazon_group = []

    black = False
    for black_asin in black_asins:
        if asin == black_asin.strip():
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
            if not obj.in_black_list:
                obj.in_black_list = True
                obj.save()
            return False, '商品グループがブラックリストに含まれています。'
    except:
        pass

    if obj.brand:
        try:
            brand_name = Q10BrandCode.objects.filter(code=obj.brand)[0].brand_name
        except Exception as e:
            print(e)
            brand_name = ''
            pass
    else:
        brand_name = ''

    black = False
    black_keyword = ''
    for black_word in black_maker_item_name:
        for desc in obj.description.split('\n'):
            if black_word in desc:
                black_keyword = black_word
                black = True
        if black:
            break

        if black_word in obj.product_name or black_word in brand_name:
            black_keyword = black_word
            black = True
            break
    if black:
        if not obj.in_black_list:
            obj.in_black_list = True
            obj.save()

        return False, f'商品名またはメーカ名にブラックリストキーワードが入っています。{black_word}'

    user_price = to_user_price(user_obj, obj.price)
    if user_price == 0:
        return False, f'最低価格以下または最高価格以上の商品です。({user_price}円)'

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
        'ItemDescription': desc_header + '<br>'+ html + '<br>' + desc_footer,
        'AdditionalOption': '',
        'ItemType': '',
        'RetailPrice': 0,
        'ItemPrice': float(to_user_price(user_obj, int(float(obj.price)))),
        'ItemQty': int(stock_num),
        'ShippingNo': int(shipping_code),
        'AvailableDateType': '0',
        'AvailableDateValue': '20:00',
        'Keyword': obj.product_name[:30]
    }

    res = requests.post('https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ItemsBasic.SetNewGoods',
                        headers=header, data=data).json()

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

        return True, ''
    else:
        try:
            if 'Can not register the goods' in res['ResultMsg']:
                return False, res['ResultMsg']
        except:
            pass

        try:
            if 'The number of registered items has been exceeded' in res['ResultMsg']:
                return False, '出品上限数を超えています。'
        except:
            pass

        try:
            if res['ResultMsg'] != '':
                return False, res['ResultMsg']
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
    # else:
    #     item_link_obj.still_getting = True
    #     item_link_obj.save()

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
        try:
            products = api.query(asin_list, wait=True, domain='JP')
        except:
            return False, []

        temp = {}
        for product in products:
            temp[product['asin']] = {
                "ok": False
            }

            try:
                temp[product['asin']]['productGroup'] = product['productGroup']
            except:
                continue

            try:
                temp[product['asin']]['brand'] = product['brand']
            except:
                temp[product['asin']]['brand'] = ''

            t, m = keepa_info(product)

            if t:
                temp[product['asin']]['links'] = t[0]
                temp[product['asin']]['description'] = t[1]
                temp[product['asin']]['jan'] = t[2]
                temp[product['asin']]['category_tree'] = t[3]
            else:
                continue

            temp[product['asin']]['ok'] = True

        return temp

    def update_listing(asin_):
        # AsinListに追加
        temp = listing_obj.asin_list.split(',')
        temp.append(asin_)
        listing_obj.asin_list = ','.join(temp)
        listing_obj.save()

    fin = {}
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
            asin_list = [val[0] for val in temp_list]
            print(asin_list)
            res = keepa_fun(asin_list)

            for temp in temp_list:
                if res[temp[0]]['ok']:
                    fin[temp[0]] = {
                        "product_name": temp[1][0],
                        "brand": temp[1][1],
                        "jan": res[temp[0]]['jan'],
                        "q10_category": temp[1][4],
                        "price": temp[1][5],
                        "productGroup": res[temp[0]]['productGroup'],
                        "links": res[temp[0]]['links'],
                        "description": res[temp[0]]['description'],
                        "category_tree": res[temp[0]]['category_tree'],
                        "brand_name": res[temp[0]]['brand'],
                    }

            temp_list = []

    for asin in fin.keys():
        try:
            temp = fin[asin]
            obj = AsinModel()
            obj.asin = asin
            obj.product_name = temp['product_name']
            obj.brand = temp['brand']
            obj.jan = temp['jan']
            obj.q10_category = '320001763'
            obj.price = int(float(temp['price']))
            obj.product_group = temp['productGroup']
            obj.description = '\n'.join(temp['description'])
            obj.photo_list = '\n'.join(temp['links'])
            obj.category_tree = temp['category_tree']

            obj.save()
            update_listing(asin)
        except Exception as e:
            print('LINK失敗', str(e))
            continue

        try:
            Q10BrandCode(code=temp['brand'], brand_name=temp['brand_name']).save()
        except:
            print('brandしぱい')


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
    user_obj: UserModel = UserModel.objects.get(username=username)
    delete_or_not = user_obj.delete_or_not

    log_success = []
    log_failed = []
    log_total = []

    def add_log(ok, key, reason=''):
        log_total.append(key)
        if ok:
            log_success.append([key, reason])
        else:
            log_failed.append([key, reason])

    try:
        user_obj: UserModel = UserModel.objects.get(username=username)
        initial_letter = user_obj.initial_letter
    except:
        return

    listing_obj: ListingModel = ListingModel.objects.get(username=username)
    listing_obj.asin_list = ','.join(list(dict.fromkeys(listing_obj.asin_list.split(','))))
    listing_obj.save()
    asin_list = listing_obj.asin_list.split(',')

    for asin in asin_list:
        try:
            msg = ''
            try:
                asin_obj: AsinModel = AsinModel.objects.get(asin=asin)
            except:
                add_log(False, asin, '存在しないASIN')
                continue

            update_available_data_type(certification_key, initial_letter + asin[1:])

            user_price = to_user_price(user_obj, asin_obj.price)
            if asin_obj.price == 0 or user_price == 0:
                if delete_or_not:
                    temp_res = delete_item(certification_key, initial_letter + asin[1:])
                    if type(temp_res) is bool:
                        asin_list_ = listing_obj.asin_list.split(',')
                        asin_list_.remove(asin) if asin in asin_list_ else asin_list_
                        listing_obj.asin_list = ','.join(asin_list_)
                        listing_obj.save()
                    else:
                        add_log(False, asin, 'Q10上から削除失敗')
                    continue
                else:
                    # 在庫を０に
                    link = 'https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0' \
                           f'&method=ItemsOrder.SetGoodsPriceQty&key={certification_key}&SellerCode={initial_letter + asin[1:]}' \
                           f'&Qty=0'
                    msg = '在庫切れ'
            elif not is_in_black(user_obj, asin_obj)[0]:
                link = 'https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0' \
                       f'&method=ItemsOrder.SetGoodsPriceQty&key={certification_key}&SellerCode={initial_letter + asin[1:]}' \
                       f'&Qty=0'
                msg = 'ブラックリスト商品'
                if not asin_obj.in_black_list:
                    asin_obj.in_black_list = True
                    asin_obj.save()
            else:
                link = 'https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi?v=1.0' \
                       f'&method=ItemsOrder.SetGoodsPriceQty&key={certification_key}&SellerCode={initial_letter + asin[1:]}' \
                       f'&Price={user_price}&Qty={user_obj.stock_num}'
                msg = f'価格改定→{user_price}'

            res = requests.get(link).json()

            if 'ResultCode' in res.keys() and res['ResultCode'] == 0:
                add_log(True, asin, msg)
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
    log_total_list.extend([val[0] for val in log_success])
    cause_list = ''
    success_list = ''
    for val in log_failed:
        cause_list += f'{val[0]}:{val[1]}{delimiter}'
    for val in log_success:
        success_list += f'{val[0]}:{val[1]}{delimiter}'

    print(log_total)
    print(cause_list)
    print(success_list)
    LogModel(username=username, type='価格改定', input_asin_list=','.join(log_total_list),
             success_asin_list=success_list , cause_list=cause_list,
             date=datetime.datetime.now()).save()


# 自動購入関連
def get_new_orders(username):
    cert_key = get_certification_key(username)

    if cert_key != '':
        header = {
            "Content-Type": 'application/x-www-form-urlencoded',
            "QAPIVersion": '1.0',
            'GiosisCertificationKey': cert_key
        }

        now = datetime.datetime.now()
        data = {
            "ShippingStat": "2",
            "search_Sdate": (now - datetime.timedelta(days=20)).strftime('%Y%m%d'),
            "search_Edate": now.strftime('%Y%m%d'),
        }

        try:
            return requests.post(
                    'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ShippingBasic.GetShippingInfo_v2',
                    headers=header, data=data
                ).json()['ResultObject']
        except:
            pass

    return []


def cancel_order(username, contract_number, message):
    header = {
        "Content-Type": 'application/x-www-form-urlencoded',
        "QAPIVersion": '1.0',
        'GiosisCertificationKey': get_certification_key(username)
    }

    data = {
        "ContrNo": contract_number,
        "SellerMemo": message,
    }

    res = requests.post('https://api.qoo10.jp//GMKT.INC.Front.QAPIService/ebayjapan.qapi/Claim.SetCancelProcess',
                        headers=header, data=data).json()

    if 'ResultCode' in res.keys() and res['ResultCode'] == 0:
        return True, ''
    else:
        if 'ResultMsg' in res.keys():
            return False, res['ResultMsg']

        return False, ''


# 発送確認処理
def send_order(username, order_no):
    cert_key = get_certification_key(username)

    if cert_key != '':
        header = {
            "Content-Type": 'application/x-www-form-urlencoded',
            "QAPIVersion": '1.0',
            'GiosisCertificationKey': cert_key
        }

        data = {
            "OrderNo": order_no,
            "ShippingCorp": 'その他',
            "TrackingNo": " "
        }

        try:
            return requests.post(
                'https://api.qoo10.jp/GMKT.INC.Front.QAPIService/ebayjapan.qapi/ShippingBasic.SetSendingInfo',
                headers=header, data=data
            ).json()
        except:
            pass

    return {}
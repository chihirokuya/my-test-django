from sp_api.api import Catalog, Products
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiRequestThrottledException, SellingApiBadRequestException, \
    SellingApiForbiddenException, SellingApiServerException, SellingApiTemporarilyUnavailableException
import keepa
import time
import random


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
            print(e)

        product_name = product_name.replace(brand, '')

        try:
            product_group = catalog['AttributeSets'][0]['ProductGroup']
        except Exception as e:
            product_group = ''
            print(e)

        return True, [product_name, brand, product_group]


# return [商品名, 価格, ブランド, Amazonグループ]　または　空
def get_from_sp_api(asin):
    result = []

    sp_api = SpApiFunction()

    offers = sp_api.get_offers(asin)
    catalog = sp_api.get_catalog(asin)

    if offers is None or catalog is None:
        return result

    if offers.errors is not None or catalog.errors is not None:
        return result

    price = sp_api.get_lowest_price(offers.payload)

    if price == '':
        return result

    ok, values = sp_api.get_from_catalog(catalog.payload)

    if not ok or values[0] == '':
        return result

    return [values[0], int(float(price)), values[1], values[2]]


#
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
        return result

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

    return [links, description, jan, category_tree]


def get_info_from_amazon(to_search_class, asin_list):
    # まずSP-APIから取得できるか確認→取得できたもののみKeepaからも取得

    print('####### Amazonから取得 #########')
    print('取得ASINリスト', asin_list)
    # SP-APIから成功したリスト、[ [asin, [商品名, 価格, ブランド, Amazonグループ]] ]
    for asin in asin_list:
        result = get_from_sp_api(asin)

        # 成功したら
        if result:
            to_search_class.result_list[asin] = {
                "name": result[0],
                "price": result[1],
                "brand": result[2],
                "group": result[3]
            }
        # 何らかの理由でエラーが出た場合
        else:
            to_search_class.to_delete_asin_list.append(asin)

    # 成功したASINリスト
    succeed_asin_list = list(to_search_class.result_list.keys())
    # ASINを10個ずつに分ける
    temp = []
    for i in range(0, len(succeed_asin_list), 10):
        temp.append(succeed_asin_list[i:i + 10])

    keepa_key = 'e4s4q8m7evnnrdsn095aj3llhbcmsqa13v0f5igam6vnomlplb970pduatfrdbi9'
    api = keepa.Keepa(keepa_key)

    for asins in temp:
        try:
            products = api.query(asins, wait=True, domain='JP')
        except:
            for asin in asins:
                to_search_class.to_delete_asin_list.append(asin)
            continue

        for product in products:
            result = keepa_info(product)

            if result:
                to_search_class.result_list[product['asin']]['links'] = result[0]
                to_search_class.result_list[product['asin']]['description'] = result[1]
                to_search_class.result_list[product['asin']]['jan'] = result[2]
                to_search_class.result_list[product['asin']]['category_tree'] = result[3]
            else:
                to_search_class.to_delete_asin_list.append(product['asin'])

    print('ASIN取得完了')
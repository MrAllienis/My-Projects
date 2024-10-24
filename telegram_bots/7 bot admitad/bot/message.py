import requests
import random
import pandas as pd
import os
import re
import psycopg2
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from image_c import add_text
from db_con import select_from_db, get_image_xlsx, select_products, update_database_coupons, save_products_to_db, save_shops_only, categories_shop, shop_go_out



MAX_CAPTION_LENGTH = 1024


access_token = 'OZ55FaZzompbqb03q8BE2QXHATp9Zq'

# Параметры запроса
params = {
    # 'region': 'RU',  # Попробуйте изменить на другой регион, например, 'RU'
    'limit': 500,
    # 'currancy': 'RUB'# Увеличьте лимит для получения большего количества купонов
    # 'language': 'ru',
}

# Заголовки запроса
headers = {
    'Authorization': f'Bearer {access_token}'
}




# def get_promocode_by_id(id):
#     # URL для запроса
#     url = f'https://api.admitad.com/coupons/{id}/'
#     # Выполнение GET-запроса
#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         print(data)
#     else:
#         print('Ошибка при выполнении запроса:', response.status_code, response.text)



def load_template_coupon(promocode):
    if promocode.upper() not in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН']:
        file_path = 'шаблон поста с промокодами.xlsx'
    else:
        file_path = 'шаблон поста с ссылкой.xlsx'
    # Чтение файла Excel
    df = pd.read_excel(file_path)
    try:
        column1 = random.choice(df.iloc[1:, 0].dropna().tolist())
    except:
        column1 = ''
    column2 = df.iloc[1:, 1].dropna().tolist()[0]
    column3 = df.iloc[1:, 2].dropna().tolist()[0]
    try:
        column4 = random.choice(df.iloc[1:, 3].dropna().tolist())
    except:
        column4 = ''
    try:
        column5 = random.choice(df.iloc[1:, 4].dropna().tolist())
    except:
        column5 = ''
    try:
        column6 = random.choice(df.iloc[1:, 5].dropna().tolist())
    except:
        column6 = ''
    column7 = df.iloc[1:, 6].dropna().tolist()[0]
    return column1, column2, column3, column4, column5, column6, column7



def load_template_products():
    file_path = 'шаблон поста с товарами.xlsx'
    # Чтение файла Excel
    df = pd.read_excel(file_path)
    try:
        column1 = random.choice(df.iloc[1:, 0].dropna().tolist())
    except:
        column1 = ''
    column2 = df.iloc[1:, 1].dropna().tolist()[0]
    column3 = df.iloc[1:, 2].dropna().tolist()[0]
    try:
        column4 = random.choice(df.iloc[1:, 3].dropna().tolist())
    except:
        column4 = ''
    try:
        column5 = random.choice(df.iloc[1:, 4].dropna().tolist())
    except:
        column5 = ''
    column6 = df.iloc[1:, 5].dropna().tolist()[0]

    return column1, column2, column3, column4, column5, column6


def get_advcampaigns_for_website2():
    url = f'https://api.admitad.com/advcampaigns/website/2684875/'
    url2 = f'https://api.admitad.com/advcampaigns/website/2699456/'
    response = requests.get(url, headers=headers, params=params)
    response2 = requests.get(url2, headers=headers, params=params)
    if response.status_code == 200 and response2.status_code == 200:
        data = response.json()
        for_delete, not_rub = save_products_to_db(data)
        data2 = response2.json()
        for_delete2, not_rub2 = save_products_to_db(data2)
        return for_delete+for_delete2, not_rub+not_rub2
    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)


def update_token():
    global access_token
    global headers
    # Ваши учетные данные
    client_id = 'Lu2OYUXBfIctB4y1lwGWpBIeW86n4t'
    client_secret = 'jxuth8PzNoEA984GcMBwxIjClFNzup'

    # URL для получения токена
    url = 'https://api.admitad.com/token/'

    # Параметры запроса
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'advcampaigns advcampaigns_for_website banners websites coupons coupons_for_website public_data'
    }

    # Отправка POST-запроса для получения токена
    response = requests.post(url, data=payload)

    # Проверка ответа
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        print('Токен доступа обновлен')
    else:
        print('Ошибка при получении токена:', response.status_code, response.text)




def get_advcampaigns_for_website():
    url = f'https://api.admitad.com/advcampaigns/website/2684875/'
    url2 = f'https://api.admitad.com/advcampaigns/website/2699456/'
    response = requests.get(url, headers=headers, params=params)
    response2 = requests.get(url2, headers=headers, params=params)
    if response.status_code == 200 and response2.status_code == 200:
        data = response.json()
        save_shops_only(data)
        data2 = response2.json()
        save_shops_only(data2)
        go_out_shops = shop_go_out(data['results']+data2['results'])
        return go_out_shops
    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)
        if response.status_code == 401:
            update_token()
        return None



def get_categories_coupons():
    url = 'https://api.admitad.com/coupons/categories/'
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = list(row['id'] for row in response.json()['results'])
        return data

def get_coupons():
    go_out_shops = get_advcampaigns_for_website()
    if go_out_shops is None:
        go_out_shops = get_advcampaigns_for_website()
    # URL для запроса
    ids_categories = get_categories_coupons()
    urls = ['https://api.admitad.com/coupons/website/2684875/', 'https://api.admitad.com/coupons/website/2699456/']
    # Выполнение GET-запроса
    data = []
    count_response = 0
    for url in urls:
        for idc in ids_categories:
            params2 = {
                # 'region': 'RU',  # Попробуйте изменить на другой регион, например, 'RU'
                'limit': 500,  # Увеличьте лимит для получения большего количества купонов
                # 'language': 'ru',
                'category': idc,
            }
            if count_response > 100:
                print('Было выполнено 100 запросов, ждём 5 секунд...')
                time.sleep(5)
            response = requests.get(url, headers=headers, params=params2)
            count_response += 1
            if response.status_code == 200:
                data.extend(response.json()['results'])
                # index = random.randint(0, len(data['results']))
                # index = 0
            else:
                print('Ошибка при выполнении запроса:', response.status_code, response.text)
    if len(data) > 0:
        messages_for_deleting, text = update_database_coupons(data)
        return messages_for_deleting, text, go_out_shops
    else:
        print('Купоны не найдены.')
        print(data)




def contains_russian(text):
    # Регулярное выражение для поиска русских символов
    russian_pattern = re.compile('[А-Яа-яЁё]')
    return bool(russian_pattern.search(text))

def create_product(post_link=False):
    message = ''
    image, name_shop, name_product, price, old_price, url, legal_info, ref_link, product_id = select_products(post_link=post_link)
    start, name_temp, price_temp, link_text, call, end = load_template_products()
    if ('' not in [image, name_shop, name_product, price, url, legal_info]) and (None not in [image, name_shop, name_product, price, url, legal_info]) and (contains_russian(name_product)):
        if start != '':
            start = start.replace('{название оффера}', f'<b>{name_shop}</b>')
            message += f'{start}\n\n'
        name_temp = name_temp.replace('{название товара}', f'<b>{name_product}</b>')
        message += f'{name_temp}\n\n'
        try:
            if (old_price not in [None, '']) and (old_price > price):
                price_temp = price_temp.replace('{цена товара}', f'<s>{str(old_price)}</s> <b>{str(price)}</b> RUB')
            else:
                price_temp = price_temp.replace('{цена товара}', f'<b>{str(price)}</b> RUB')
        except:
            price_temp = price_temp.replace('{цена товара}', f'<b>{str(price)}</b> RUB')
        message += f'{price_temp}\n\n'
        link_text = link_text.replace('ссылке', f'<a href="{url}">ссылке</a>')
        message += f'{link_text}\n\n'
        if call != '':
            temps = ['{ТОВАРЫ}', '{боте}', '{бот}', '{бота}', '{ботом}']
            for temp in temps:
                if temp in call:
                    call = call.replace(temp, f'<a href="https://t.me/products186_bot">{temp[1:-1].upper()}</a>')
            call = call.replace('~', '')
            message += f'<blockquote><i>{call}</i></blockquote>\n\n'
        end = end.replace('{реквизиты оффера}', legal_info)
        end = end.replace('{название магазина}', name_shop)
        # parsed_url = urlparse(url)
        # params = parse_qs(parsed_url.query)
        # # Получение значения 'erid'
        # erid_value = params.get('erid', [None])[0]
        # end = end.replace('{N erid}', erid_value)
        message += end
        type = 'product'
        image = add_text(image, end, type)
        if len(message) > MAX_CAPTION_LENGTH:
            message = ''
    return image, message, product_id


def create_message(promo=False, admin_post=False):
    message = f''
    image = None
    date_end = None
    coupon_id = None
    try:
        coupon_id, campaign_name, discount, name, condition, date_start, date_end, ref_link, legal_info, promocode = select_from_db(promo=promo, name_promo=admin_post)
        start, desc1, desc_cond, desk_link, link_text, call, end = load_template_coupon(promocode)
        image = get_image_xlsx(campaign_name)
        if ('' not in [name, link_text, legal_info, discount]) and (None not in [name, link_text, legal_info, discount]) and (contains_russian(name)):
            if start != '':
                start = start.replace('{n%}', f'<b>{discount}</b>')
                start = start.replace('{название оффера}', f'<b>{campaign_name}</b>')
                message += f'{start}\n\n'

            if promocode.upper() not in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН']:
                desc1 = desc1.replace('{промокод} - {описание промокода}', f'<code>{promocode}</code> - {name}')
            else:
                desc1 = desc1.replace('{описание промокода}', name)

            message += f'{desc1}\n\n'
            if condition != '':
                desc_cond = desc_cond.replace('{условие купона}', condition)
                message += f'{desc_cond}\n\n'
            if desk_link != '':
                message += f'{desk_link}\n\n'
            link_text = link_text.replace('ссылке', f'<a href="{ref_link}">ссылке</a>')
            message += f'{link_text}\n\n'
            if call != '':
                temps = ['{ПРОМОКОДЫ}', '{боте}', '{промокодами}', '{бот}', '{бота}', '{здесь}']
                for temp in temps:
                    if temp in call:
                        call = call.replace(temp, f'<a href="https://t.me/coupons186_bot">{temp[1:-1].upper()}</a>')
                call = call.replace('~', '')
                message += f'<blockquote><i>{call}</i></blockquote>\n\n'

            end = end.replace('{реквизиты оффера}', legal_info)
            end = end.replace('{название магазина}', f'{campaign_name}')
            # parsed_url = urlparse(ref_link)
            # params = parse_qs(parsed_url.query)
            # # Получение значения 'erid'
            # erid_value = params.get('erid', [None])[0]
            # end = end.replace('{N erid}', erid_value)
            message += end
            type = 'coupon'
            image = add_text(image, end, type)
            if len(message) > MAX_CAPTION_LENGTH:
                message = ''
    finally:
        return image, message, date_end, coupon_id


if __name__ == '__main__':
    print(get_coupons())
import requests




access_token = 'aWvKxovxbVGZrmrRdysvVhX4lSKBhx'

# Параметры запроса
params = {
    # 'region': 'RU',  # Попробуйте изменить на другой регион, например, 'RU'
    'limit': 300,  # Увеличьте лимит для получения большего количества купонов
    # 'language': 'ru',
}

# Заголовки запроса
headers = {
    'Authorization': f'Bearer {access_token}'
}

def get_campaign(campaign_id):
    # Выполнение GET-запроса
    url = f'https://api.admitad.com/advcampaigns/{campaign_id}/website/2683345/'
    response = requests.get(url, headers=headers, params=params)
    # Проверка ответа
    if response.status_code == 200:
        data = response.json()
        # print(data)
        ref_link = data['gotolink']
        # ic(data['products_csv_link'])
        # ic(data['products_xml_link'])
        legal_info = data['advertiser_legal_info']
        # ic(data['description'])
        return ref_link, legal_info
    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)


def get_promocode_by_id(id):
    # URL для запроса
    url = f'https://api.admitad.com/coupons/{id}/'
    # Выполнение GET-запроса
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        print(data)
        # if data['_meta']['count'] > 0:
        #     print('Данные:', data)
        #     pass
        # else:
        #     print('Купоны не найдены.')
    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)


def get_coupons():
    # URL для запроса
    url = f'https://api.admitad.com/coupons/website/2683345/'
    # Выполнение GET-запроса
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['_meta']['count'] > 0:
            print('Данные:', data)
            ref_link, legal_info = get_campaign(data['results'][0]['campaign']['id'])
            print(ref_link, legal_info)
        else:
            print('Купоны не найдены.')
            print(data)
    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)


if __name__ == '__main__':
    # get_promocode_by_id(595790)
    get_coupons()
import requests
from icecream import ic


access_token = '6RjaL0hv7JWV6IvS3Ngk0q4SGctFEV'

# URL для запроса
# url = 'https://api.admitad.com/websites/v2/2683345/'
# url = 'https://api.admitad.com/advcampaigns/17167/'
url = 'https://api.admitad.com/advcampaigns/website/2683345/'


# 35530 Идентификатор партнерской программы

# Параметры запроса (увеличиваем лимит и проверяем другой регион)
params = {
    'region': 'RU',
    'limit': 100,
    # 'website': '2683345',
    'language': 'ru',
}

# Заголовки запроса
headers = {
    'Authorization': f'Bearer {access_token}'
}


def get_campaign():
    # Выполнение GET-запроса
    # url = f'https://api.admitad.com/advcampaigns/{campaign_id}/website/2683345/'
    response = requests.get(url, headers=headers, params=params)

    # Проверка ответа
    if response.status_code == 200:
        data = response.json()
        # print(data)
        # ic(data['gotolink'])
        # ic(data['products_csv_link'])
        # ic(data['products_xml_link'])
        # ic(data['advertiser_legal_info'])
        # ic(data['description'])
        print(data)

    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)

get_campaign()

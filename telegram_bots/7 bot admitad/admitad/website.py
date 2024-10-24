import requests
from icecream import ic


access_token = '6RjaL0hv7JWV6IvS3Ngk0q4SGctFEV'

# URL для запроса
url = 'https://api.admitad.com/websites/v2/'

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

# Выполнение GET-запроса
response = requests.get(url, headers=headers, params=params)

# Проверка ответа
if response.status_code == 200:
    data = response.json()
    print(data)



    # if data['_meta']['count'] > 0:
    #     # print('Данные:', data)
    #     pass
    # else:
    #     print('Купоны не найдены.')
else:
    print('Ошибка при выполнении запроса:', response.status_code, response.text)

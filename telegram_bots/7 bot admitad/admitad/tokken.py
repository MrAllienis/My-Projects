import requests
from requests.auth import HTTPBasicAuth


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
    access_token = token_info
    print('Токен доступа:', access_token)
else:
    print('Ошибка при получении токена:', response.status_code, response.text)

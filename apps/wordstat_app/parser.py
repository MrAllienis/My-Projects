import requests
import re
from urllib.parse import quote
import pandas as pd
import main3
import openpyxl
from openpyxl import load_workbook
import pandas as pd
import time


url = 'https://wordstat-2.yandex.ru/?region=all&view=graph&words=%D0%BA%D1%83%D0%BF%D0%B8%D1%82%D1%8C'

result_data = {}

def get_json(url):
    quoted_list = ['"' + item + '"' for item in main3.full_all_phrases]
    print(f"Всего фраз: {len(main3.full_all_phrases)}")
    print('')

    cookies = {
        'yandexuid': '1417398311704753732',
        'yuidss': '1417398311704753732',
        'ymex': '2020113732.yrts.1704753732',
        'gdpr': '0',
        '_ym_uid': '170483944186249277',
        'yashr': '961279391704839442',
        'amcuid': '8898487801705165494',
        'i': 'Z3ENcrHqxcwaDi0UNbTZvtcJybHZLt6DYH8KKYL0+0d2m8tFBAcVOR5d+2E7NVAI/4hNNdijghMi2XhUP6Z2J9cz9AA=',
        'font_loaded': 'YSv1',
        'yandex_gid': '172',
        'my': 'YwA=',
        'bltsr': '1',
        'KIykI': '1',
        '_ym_isad': '1',
        'is_gdpr': '1',
        'is_gdpr_b': 'COOiFBDy6wEYASgC',
        '_ym_d': '1708297529',
        '_ym_visorc': 'b',
        '_yasc': '7sHftOTENpvn6qt0Qr/9VsPKZMxfjS/RH6u2cGTQEqm4fMVlKrCXdWgy5RVY3e7ImHzhbCnJRkzLDoikzRNNLZwD0m6m',
        'bh': 'Ej8iTm90IEEoQnJhbmQiO3Y9Ijk5IiwiR29vZ2xlIENocm9tZSI7dj0iMTIxIiwiQ2hyb21pdW0iO3Y9IjEyMSIaBSJ4ODYiIhAiMTIxLjAuNjE2Ny4xODUiKgI/MDICIiI6CSJXaW5kb3dzIkIIIjEwLjAuMCJKBCI2NCJSXCJOb3QgQShCcmFuZCI7dj0iOTkuMC4wLjAiLCJHb29nbGUgQ2hyb21lIjt2PSIxMjEuMC42MTY3LjE4NSIsIkNocm9taXVtIjt2PSIxMjEuMC42MTY3LjE4NSIi',
        'Session_id': '3:1708299133.5.3.1705080088255:Mu8pXg:6.1.2:1|1706604335.0.2.3:1705080088|229472572.1971688.2.2:1971688.3:1707051776|46383387.1971840.2.2:1971840.3:1707051928|1950788281.3219045.2.2:3219045.3:1708299133|3:10283313.81972.DICkvxjht1RHibWjhL8r2bZDgwI',
        'sessar': '1.1187.CiDCFeRzewhhe9ZH_O583YinbrJMMddkMjtu-SdOH_OHpQ.bB8qH5GSErv6PKl8CKvWtgin2mQ1zvvq2kVs7eJ0Trg',
        'sessionid2': '3:1708299133.5.3.1705080088255:Mu8pXg:6.1.2:1|1706604335.0.2.3:1705080088|229472572.1971688.2.2:1971688.3:1707051776|46383387.1971840.2.2:1971840.3:1707051928|1950788281.3219045.2.2:3219045.3:1708299133|3:10283313.81972.fakesign0000000000000000000',
        'yp': '1723614207.szm.1:1920x1080:1920x953#1710975952.csc.2#2023361960.pcs.0#1710680360.hdrc.0#2023659133.udn.cDphd2Vzb21lLjEyMzMxMjIz#2023659133.multib.1',
        'L': 'WiZqZEBdbWZtbwFlYVx3UURuXX9iUF4HDjUUAh06IUoHdnllcHx5cA==.1708299133.15623.35862.9818e67aecf283e22977602a23c433f8',
        'yandex_login': 'awesome.12331223',
        'ys': 'udn.cDphd2Vzb21lLjEyMzMxMjIz#c_chck.1837542935',
    }

    index0 = 1
    for index, text in enumerate(quoted_list):
        # time.sleep(1)
        # Кодирование строки
        encoded_string = quote(text, encoding='utf-8')
        # print(encoded_string)

        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            # 'Cookie': 'yandexuid=1417398311704753732; yuidss=1417398311704753732; ymex=2020113732.yrts.1704753732; gdpr=0; _ym_uid=170483944186249277; yashr=961279391704839442; amcuid=8898487801705165494; instruction=1; L=QVVdXWZneVheWE5iR3F7RVpdWlteU1tLGAcfLhsMJgUvESQpLSJdBQ==.1707064570.15609.346960.07d2ad9564c8c3b85aad8f93f46e60f9; yandex_login=allthisfbranches; i=Z3ENcrHqxcwaDi0UNbTZvtcJybHZLt6DYH8KKYL0+0d2m8tFBAcVOR5d+2E7NVAI/4hNNdijghMi2XhUP6Z2J9cz9AA=; font_loaded=YSv1; yandex_gid=172; my=YwA=; _ym_d=1707846198; yp=1723614207.szm.1:1920x1080:1920x953#1710524619.csc.1; ys=udn.cDpyYXlxdmF6YQ%3D%3D#c_chck.1616758966; is_gdpr=0; is_gdpr_b=COOiFBD46gEoAg==; Cookie_check=AixscM31; Session_id=3:1707918681.5.0.1705080088255:Mu8pXg:6.1.2:1|1706604335.0.2.3:1705080088|229472572.1971688.2.2:1971688.3:1707051776|46383387.1971840.2.2:1971840.3:1707051928|3:10283101.626525.foSJILDRyGGYJLPcPjyghg1oRLI; sessar=1.1186.CiDXw1CwmYhYJ5qngwpAuSc9CQzymDajpdUvQ3DKBnhUhg.EFVvyU0WTl6VgiAL1qHfWtgCQnIa4A8cmg-bq3lxjQw; sessionid2=3:1707918681.5.0.1705080088255:Mu8pXg:6.1.2:1|1706604335.0.2.3:1705080088|229472572.1971688.2.2:1971688.3:1707051776|46383387.1971840.2.2:1971840.3:1707051928|3:10283101.626525.fakesign0000000000000000000; _ym_isad=1; _ym_visorc=w; bh=Ej8iTm90IEEoQnJhbmQiO3Y9Ijk5IiwiR29vZ2xlIENocm9tZSI7dj0iMTIxIiwiQ2hyb21pdW0iO3Y9IjEyMSIaBSJ4ODYiIhAiMTIxLjAuNjE2Ny4xNjIiKgI/MDICIiI6CSJXaW5kb3dzIkIIIjEwLjAuMCJKBCI2NCJSXCJOb3QgQShCcmFuZCI7dj0iOTkuMC4wLjAiLCJHb29nbGUgQ2hyb21lIjt2PSIxMjEuMC42MTY3LjE2MiIsIkNocm9taXVtIjt2PSIxMjEuMC42MTY3LjE2MiIi; _yasc=8vXFTsxzs0tLDMN2RuBO/BFpDOS7hs2BqZOsDLG6BHEFAEyrOCMRP8ER97wQyjm3A6SpNhVpPDJMyPpmDjSs1KS5GA==',
            'DNT': '1',
            'Origin': 'https://wordstat-2.yandex.ru',
            'Pragma': 'no-cache',
            'Referer': f'https://wordstat-2.yandex.ru/?region=all&view=graph&words={encoded_string}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            }

        json_data = {
                'currentDevice': 'desktop,phone,tablet',
                'currentGraphType': 'month',
                'currentMapType': 'all',
                'filters': {
                    'region': 'all',
                    'tableType': 'popular',
                },
                'searchValue': f'{text}',
                'startDate': '01.02.2022',
                'endDate': '31.01.2024',
                'text': {
                    'graph': {
                        'title': 'История запросов «»',
                        'disclaimer': 'Для каждой даты с 01.02.2022 по 31.01.2024 мы посчитали отношение числа запросов «» к среднему числу таких запросов за весь период.\\nГрафик показывает, как отличается дневное количество запросов от среднего значения.',
                    },
                    'map': {
                        'title': '',
                        'disclaimer': '',
                    },
                    'table': {
                        'title': '',
                        'disclaimer': '',
                    },
                },
            }

        response = requests.post('https://wordstat-2.yandex.ru/wordstat/api/search', cookies=cookies, headers=headers, json=json_data)
        data = response.json()


        try:
            text1 = data['table']['tableData']['popular'][0]['text']
            value1 = data['totalValue']
            value2 = int(data['table']['tableData']['popular'][0]['value'])
            text2 = text[1:-1]
            result_data[index0]= [text1, value1, value2, text2]
            print(f'{index0} | ===== | {text2} | ОБРАБОТАН УСПЕШНО! | ===== |')
            index0 += 1
        except:
            print(f'Совпадение для значения {text} не найдено')



        df = pd.DataFrame(result_data)
        df = pd.DataFrame(result_data.values(),  columns=["Фраза WordStat", "В кавычках", "Без кавычек", "Исходник"])
        column_widths = [15, 10, 10, 15]
        df = df[["Фраза WordStat", "В кавычках", "Без кавычек", "Исходник"]]
        df.to_excel("wordstat.xlsx", index=False)

    print(result_data)
    time.sleep(2)
    input("Нажмите 'Enter' для выхода из программы")






if __name__ == "__main__":
    # main()
    get_json('https://wordstat-2.yandex.ru/wordstat/api/search')

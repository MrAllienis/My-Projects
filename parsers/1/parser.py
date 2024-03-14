import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook



links_to_pars = []
finish_data2 = {}

class Parser:

    mega_link = [
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=1',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=2',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=3',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=4',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=5',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=6',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=7',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=8',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=9',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=10',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=11',
                 # 'https://www.vilon.ru/catalog/?PAGEN_3=12',
                 'https://www.vilon.ru/catalog/?PAGEN_3=13',
                 'https://www.vilon.ru/catalog/?PAGEN_3=14'
                 ]


    @staticmethod
    def get_eat_by_link(link, key, ws):
        response = requests.get(link)
        print(response.status_code)
        if response.status_code != 200:
            return

        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        spu = ''
        category = ''
        title = ''
        text1 = ''
        text2 = ''
        text3 = ''
        price = ''
        weight = ''
        cal = ''
        bel = ''
        gir = ''
        ugl = ''
        box = ''
        year = ''
        usl = ''
        seo_title = ''
        seo_descr = ''
        seo_key = ''
        url = ''
        photos = ''
        textt = ''

        spu = soup.find_all('div', class_="recipe-sect__feck-row-value")[len(soup.find_all('div', class_="recipe-sect__feck-row-value"))-1].text
        category = soup.find_all('ul', class_="crumbs-sect__nav")[0].contents[2].text
        title = soup.find_all('ul', class_="crumbs-sect__nav")[0].contents[3].text
        text1 = soup.find_all('div', class_="catalog-sect__text")[1].text[5:]
        text2 = soup.find_all('div', class_="catalog-sect__text")[2].text[2:]
        text3 = soup.find_all('div', class_="catalog-sect__text")[3].text[2:]
        price = soup.find_all('div', class_="promo-sect__slide-price-number")[1].text
        weight = soup.find_all('div', class_="recipe-sect__feck-row-value")[0].text
        cal = soup.find_all('div', class_="recipe-sect__feck-row-value")[1].text
        bel = soup.find_all('div', class_="recipe-sect__feck-row-value")[2].text
        gir = soup.find_all('div', class_="recipe-sect__feck-row-value")[3].text
        ugl = soup.find_all('div', class_="recipe-sect__feck-row-value")[4].text
        box = soup.find_all('div', class_="recipe-sect__feck-row-value")[len(soup.find_all('div', class_="recipe-sect__feck-row-value"))-4].text
        year = soup.find_all('div', class_="recipe-sect__feck-row-value")[len(soup.find_all('div', class_="recipe-sect__feck-row-value"))-3].text
        usl = soup.find_all('div', class_="recipe-sect__feck-row-value")[len(soup.find_all('div', class_="recipe-sect__feck-row-value"))-2].text
        seo_title = soup.title.text
        seo_descr = soup.find_all()[11].attrs['content']
        seo_key = soup.find_all()[12].attrs['content']
        url = link

        textt = text1+text2+text3
        if len(soup.find_all('div', class_="thumb-item_tproduct")) == 1:
            photo1 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[0].contents[1].attrs['src']
            photoss = f'{photo1}'
            photos = photoss
        elif len(soup.find_all('div', class_="thumb-item_tproduct")) == 2:
            photo1 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[0].contents[1].attrs['src']
            photo2 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[1].contents[1].attrs['src']
            photoss = f'{photo1}, {photo2}'
            photos = photoss
        elif len(soup.find_all('div', class_="thumb-item_tproduct")) == 3:
            photo1 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[0].contents[1].attrs['src']
            photo2 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[1].contents[1].attrs['src']
            photo3 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[2].contents[1].attrs['src']
            photoss = f'{photo1}, {photo2}, {photo3}'
            photos = photoss

        elif len(soup.find_all('div', class_="thumb-item_tproduct")) == 4:
            photo1 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[0].contents[1].attrs['src']
            photo2 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[1].contents[1].attrs['src']
            photo3 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[2].contents[1].attrs['src']
            photo4 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[3].contents[1].attrs['src']
            photoss = f'{photo1}, {photo2}, {photo3}, {photo4}'
            photos = photoss
        elif len(soup.find_all('div', class_="thumb-item_tproduct")) == 5:
            photo1 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[0].contents[1].attrs['src']
            photo2 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[1].contents[1].attrs['src']
            photo3 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[2].contents[1].attrs['src']
            photo4 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[3].contents[1].attrs['src']
            photo5 = 'https://www.vilon.ru/'+soup.find_all('div', class_="thumb-item_tproduct")[4].contents[1].attrs['src']
            photoss = f'{photo1}, {photo2}, {photo3}, {photo4}, {photo5}'
            photos = photoss


        key += 1
        finish_data2[key] = []
        dates = [spu, category, title, textt, price, weight, cal, bel, gir, ugl, box, year, usl, seo_title, seo_descr, seo_key, url, photos]
        for element in dates:
            finish_data2[key].append(element)

        for row, values in finish_data2.items():
            for i, value in enumerate(values, start=1):
                ws.cell(row=int(row), column=i, value=value)



    @staticmethod
    def get_mega_link(link):
        response = requests.get(link)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        for elem in soup.find_all('a', class_="promo-sect__slide-title"):
            links_to_pars.append('https://www.vilon.ru'+elem.attrs['href'])



    def run(self):
        key = 0
        wb = Workbook()
        ws = wb.active
        for link in self.mega_link:
            self.get_mega_link(link)
        for link in links_to_pars:
            key +=1
            self.get_eat_by_link(link, key, ws)
            pass
        wb.save('VILON.xlsx')




parser1 = Parser()
parser1.run()






import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook



finish_data = {}

class Parser:
    global_key = 0
    list_of_href = []
    links_to_pars = [
            # 'https://www.lamoda.ru/c/355/clothes-zhenskaya-odezhda/',
            # 'https://www.lamoda.ru/c/15/shoes-women/',
            # 'https://www.lamoda.ru/c/557/accs-zhenskieaksessuary/',
            # 'https://www.lamoda.ru/c/1262/default-premium-women/',
            # 'https://www.lamoda.ru/c/831/default-sports-women/',
            # 'https://www.lamoda.ru/c/4308/default-krasotawoman/',
            # 'https://www.lamoda.ru/c/477/clothes-muzhskaya-odezhda/',
            # 'https://www.lamoda.ru/c/17/shoes-men/',
            # 'https://www.lamoda.ru/c/559/accs-muzhskieaksessuary/',
            # 'https://www.lamoda.ru/c/1263/default-premium-men/',
            # 'https://www.lamoda.ru/c/832/default-sports-men/',
            # 'https://www.lamoda.ru/c/4288/beauty_accs-menbeauty/',
            # 'https://www.lamoda.ru/c/5379/default-devochkam/',
            # 'https://www.lamoda.ru/c/5378/default-malchikam/',
            # 'https://www.lamoda.ru/c/5414/default-novorozhdennym/',
            # 'https://www.lamoda.ru/c/6327/default-detskieigrushki/',
            # 'https://www.lamoda.ru/c/6815/default-uhod_za_rebenkom/',
            'https://www.lamoda.ru/c/6647/home_accs-tovarydlyadoma/'
    ]
    links_to_pars2 = []


    def get_closes_by_link(self, link, index):
        response = requests.get(link)
        # print(response.status_code)
        if response.status_code != 200:
            return

        text = response.text
        soupp = BeautifulSoup(text, "html.parser")


        category = soupp.find_all('a', class_="d-header-topmenu-category__link dense")[index].text[9:][:-7]
        # category = 'Уход и косметика'
        category_title = soupp.title.text
        category_desc = soupp.title.nextSibling.attrs['content']
        category_link = soupp.find_all()[20].attrs['content']
        finish_data[self.global_key] = [category, category_title, category_desc, category_link]
        print(finish_data[self.global_key])
        orient = (len(soupp.find_all('a', class_="x-link x-link__label"))-5)

        number = 0


        # while number < orient:
        while number < 12:
            self.global_key+=1
            href = 'https://www.lamoda.ru' + (soupp.find_all('a', class_="x-link x-link__label")[0:][number].attrs['href'])
            number += 1
            response = requests.get(href)
            text = response.text
            soup = BeautifulSoup(text, "html.parser")
            category_title = soup.title.text
            category_desc = soup.title.nextSibling.attrs['content']
            new_title = soup.find_all('div', class_="x-breadcrumbs__slide")[2].text[13:][:-11]
            finish_data[self.global_key] = [category, new_title, category_title, category_desc, href]
            print(finish_data[self.global_key])
            # href2 = 'https://www.lamoda.ru' + (
            # soup.find_all('a', class_="x-link x-link__label")[1:-4][number].attrs['href'])
            # try:
            #     self.second_level(href2, category, new_title)
            # except:
            #     pass
            counter = 0
            try:
                while counter < 60:
                    href2 = 'https://www.lamoda.ru' + (soup.find_all('a', class_="x-link x-link__label")[1:][counter].attrs['href'])
                    try:
                        self.second_level(href2, category, new_title)
                    except:
                        pass
                    counter +=1
            except:
                pass







    def second_level(self, href2, category, new_title ):
        # print(href, key)
        number = 2
        response = requests.get(href2)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        new_title3 = soup.find_all('div', class_="x-breadcrumbs__slide")[3].text[13:][:-11]
        error = None
        category_title = soup.title.text
        category_desc = soup.title.nextSibling.attrs['content']
        self.global_key+=1


        finish_data[self.global_key] = [category, new_title, new_title3, category_title, category_desc, href2]
        print(finish_data[self.global_key])
        try:
            while number< 60:
                href3 = 'https://www.lamoda.ru' + (soup.find_all('a', class_="x-link x-link__label")[1:][number].attrs['href'])
                try:
                    self.third_level(href3, category, new_title, new_title3)
                except:
                    pass
                number+=1
        except:
            pass


    def third_level(self, href3, category, new_title, new_title3):
        self.global_key+=1
        response = requests.get(href3)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        category_title = soup.title.text
        category_desc = soup.title.nextSibling.attrs['content']
        new_title4 = soup.find_all('div', class_="x-breadcrumbs__slide")[4].text[13:][:-11]
        finish_data[self.global_key] = [category, new_title, new_title3, new_title4, category_title, category_desc, href3]
        print(finish_data[self.global_key])

    @staticmethod
    def save_data():
        key = 0
        wb = Workbook()
        ws = wb.active
        for row, values in finish_data.items():
            for i, value in enumerate(values, start=1):
                ws.cell(row=int(row), column=i, value=value)
        wb.save('lamoda.xlsx')


    def run(self):
        index = 6
        for link in self.links_to_pars:
            self.global_key += 1
            self.get_closes_by_link(link, index)
            index +=1





parser1 = Parser()
try:
    parser1.run()
    parser1.save_data()
except:
    parser1.save_data()


# print(finish_data)


# parser1.run()
# parser1.save_data()

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook



finish_data = {}

class Parser:
    global_key = 0
    list_of_href = []
    links_to_pars = [
            'https://www.bookvoed.ru/books?genre=2',
            # 'https://www.bookvoed.ru/books?genre=4',
            # 'https://www.bookvoed.ru/books?genre=10',
            # 'https://www.bookvoed.ru/books?genre=5',
            # 'https://www.bookvoed.ru/books?genre=6',
            # 'https://www.bookvoed.ru/books?genre=7',
            # 'https://www.bookvoed.ru/books?genre=8'
            ]
    links_to_pars2 = []


    def get_closes_by_link(self, link):
        response = requests.get(link)
        print(response.status_code)
        if response.status_code != 200:
            return

        text = response.text
        soupp = BeautifulSoup(text, "html.parser")


        category = soupp.find_all('li', class_="iK")[0].contents[2].text
        # category = 'Уход и косметика'
        category_title = soupp.title.text
        category_desc = soupp.find_all()[5].attrs['content']
        category_link = soupp.find_all('meta')[7].attrs['content']
        finish_data[self.global_key] = [category, category_title, category_desc, category_link]
        print(finish_data[self.global_key])
        orient = (len(soupp.find_all('a', class_="Rvb")))

        number = 7


        # while number < orient:
        while number < 16:
            self.global_key+=1
            href = (soupp.find_all('a', class_="Rvb"))[number].attrs['href']
            number += 1
            response = requests.get(href)
            text = response.text
            soup = BeautifulSoup(text, "html.parser")
            category_title = soup.title.text
            category_desc = soup.find_all()[5].attrs['content']
            new_title = soup.find_all('li', class_="iK")[1].contents[2].text
            finish_data[self.global_key] = [category, new_title, category_title, category_desc, href]
            print(finish_data[self.global_key])

            counter = 0
            try:
                while counter < 60:
                    href2 = (soup.find_all('a', class_="Rvb"))[counter].attrs['href']
                    try:
                        self.second_level(href2, category, new_title)
                    except:
                        pass
                    counter +=1
            except:
                pass



    def second_level(self, href2, category, new_title ):
        # print(href, key)
        number = 0
        response = requests.get(href2)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        new_title3 = soup.find_all('li', class_="iK")[2].contents[2].text

        category_title = soup.title.text
        category_desc = soup.find_all()[5].attrs['content']
        self.global_key+=1

        finish_data[self.global_key] = [category, new_title, new_title3, category_title, category_desc, href2]
        print(finish_data[self.global_key])
        try:
            while number< 60:
                href3 = (soup.find_all('a', class_="Rvb"))[number].attrs['href']
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
        category_desc = soup.find_all()[5].attrs['content']
        new_title4 = soup.find_all('li', class_="iK")[3].contents[2].text
        finish_data[self.global_key] = [category, new_title, new_title3, new_title4, category_title, category_desc, href3]
        print(finish_data[self.global_key])
        number=0
        try:
            while number< 60:
                href4 = (soup.find_all('a', class_="Rvb"))[number].attrs['href']
                try:
                    self.fourth_level(href4, category, new_title, new_title3, new_title4)
                except:
                    pass
                number+=1
        except:
            pass

    def fourth_level(self, href4, category, new_title, new_title3, new_title4):
        self.global_key+=1
        response = requests.get(href4)
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        category_title = soup.title.text
        category_desc = soup.find_all()[5].attrs['content']
        new_title5 = soup.find_all('li', class_="iK")[4].contents[2].text
        finish_data[self.global_key] = [category, new_title, new_title3, new_title4, new_title5, category_title, category_desc, href4]
        print(finish_data[self.global_key])

    @staticmethod
    def save_data():
        key = 0
        wb = Workbook()
        ws = wb.active
        for row, values in finish_data.items():
            for i, value in enumerate(values, start=1):
                ws.cell(row=int(row), column=i, value=value)
        wb.save('parser1.xlsx')


    def run(self):
        for link in self.links_to_pars:
            self.global_key += 1
            self.get_closes_by_link(link)






parser1 = Parser()
try:
    parser1.run()
    parser1.save_data()
except:
    parser1.save_data()


# print(finish_data)


# parser1.run()
# parser1.save_data()

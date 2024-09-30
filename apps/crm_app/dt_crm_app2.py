# Библиотеки
import io
import datetime
import json
import locale
import traceback
import logging
import os
import subprocess
from itertools import chain
import re
import time

import smtplib
from email.message import EmailMessage

from lxml import etree
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.common.exceptions import TimeoutException

import pandas as pd
import numpy as np

import pygsheets
from pygsheets.custom_types import FormatType
from googleapiclient.http import MediaIoBaseUpload

import requests
from requests.auth import HTTPBasicAuth

import argparse
import configparser

import mysql.connector
from mysql.connector import errorcode
import hashlib
import string
import random

from tendo import singleton

from baikal_api import BaikalApi
from gsheet_utils import GSheetUtils
import vcard_utils
from vcard_rules import VCardRuleBase

# Глобальные переменные
# Символы для генератора паролей Baikal
CHARS = list(string.ascii_letters + string.digits + "!@#$%^&*()")
# Листы в таблицах
WKSHEETS = ['Команда', 'Команда Архив', 'PV Архив', 'Изменения']
LDNAME = 'Лидеры'
ARCHNAME = 'Команда Архив'
# Колонки в таблице лидеров
LD_COLUMNS = [
    ('Имя', 'A'), ('ID', 'B'), ('DT_pass', 'C'), ('SBID', 'D'), ('URL', 'E'), ('Обновление', 'F'),
    ('Prefix', 'G'), ('К-во', 'H'), ('Baikal', 'I'), ('Baikal_user', 'J'), ('Baikal_pass', 'K'),
    ('Файл', 'L'), ('Листы', 'M'), ('Email', 'N'), ('Доступ', 'O'), ('mobileconfig', 'P'), ('Pub spreadsheet', 'Q')
]
LD_COLUMNS_ORDER = [i[0] for i in LD_COLUMNS]
# Флаг успешности операции
MSG_SUCCESS = True
# Этап, на котором застопорилось выполнение скрипта
MSG_STAGE = ''
# Текст ошибки
MSG_ERROR = ''
# Трассировка Python
MSG_TRACE = ''

# Счетчики типов ошибок
ERRCOUNT_GOOGLE = 0
ERRCOUNT_DOTERRA = 0
ERRCOUNT_BAIKAL = 0

STUCK = 0
STUCK_AT_DOTERRA = 0
STUCK_AT_BAIKAL = 0
STUCK_AT_GOOGLE = 0
STUCK_AT_GOOGLE_SUB = 0

RETRIES = 0  # До 3
RETRIES_SUB = 0

# Имена столбцов таблицы Лидеры
_NAME = 'Имя'
_ID = 'ID'
_DT_PASS = 'DT_pass'
_SBID = 'SBID'
_URL = 'URL'
_UPDATE = 'Обновление'
_BAIKAL_PREFIX = 'Prefix'
_QTY = 'К-во'
_BAIKAL_ACTIVE = 'Baikal'
_BAIKAL_USER = 'Baikal_user'
_BAIKAL_PASS = 'Baikal_pass'
_FILE = 'Файл'
_EMAIL = 'Email'
_MCONF = 'mobileconfig'
_ACCESS = 'Доступ'

# Уровень погруженности
LEVEL = 0

# Адреса администраторов
ADMIN_EMAILS = []

# Буфер
BUF = []
ERRSTACK = []

# Маркер отправки почты
EMAIL_SENT = False

# Демо-режим
DEMO_MODE = False

# Папка с файлами кеша
CACHE_DIRPATH = "www/v8/cache"


# Печать с записью в буфер и сдвигом в зависимости от уровня
def print_l(_str):
    res = LEVEL * '- ' + str(_str)
    print(res)
    BUF.append(res)
    if len(BUF) > 10:
        BUF.pop(0)


# Генератор паролей
def generate_random_password(charset):
    print_l("Генерируем новый пароль...")
    length = 12
    random.shuffle(charset)

    password = []
    for i in range(length):
        password.append(random.choice(charset))

    random.shuffle(password)
    print_l('Пароль сгенерирован.')
    return "".join(password)


# Отправка почты
# ([sta, err, tra], [sta, err, tra], [sta, err, tra], ...) = errstack
def sendMail(emIn, errstack=None, success=True):
    global EMAIL_SENT
    if not EMAIL_SENT:
        # Настройка почтового сервера
        mail_set = emIn

        _smtp_server = mail_set['server']
        _smtp_port = mail_set['port']
        fromaddr = mail_set['addr_source']
        frompass = mail_set['pass']
        toaddr = mail_set['addr_dest']

        # Формирование сообщения
        strDate = datetime.datetime.now().ctime()
        status = 'НЕИЗВЕСТНО'
        strMess = f'Это тестовое сообщение. Если вы видите его на экране, то проверка статуса по какой-либо причине не сработала.\n\nВыход консоли (для разработчика): {traceback.format_exc()}'
        if not success:
            strErrStack = [
                "ЭТАП: {}\nОШИБКА: {}\nТРАССИРОВКА: {}\n===== ===== ===== ===== =====\n".format(x[0], x[1], x[2]) for x
                in errstack]
            status = 'ОШИБКА'
            strMess = "Во время выполнения скрипта произошла критическая ошибка. Программа была аварийно завершена.\n\n" \
                      + "Обратитесь к разработчику за консультацией.\n\n" \
                      + "Последний вывод консоли:\n{}\n\n".format('\n'.join(BUF)) \
                      + "Трассировка консоли:\n{}\n\n".format(traceback.format_exc()) \
                      + "Также были выявлены следующие ошибки:\n" + "\n\n".join(strErrStack) \
                      + "Ошибок Google: {}\n".format(ERRCOUNT_GOOGLE) \
                      + "Ошибок doTERRA: {}\n".format(ERRCOUNT_GOOGLE) \
                      + "Ошибок BAIKAL: {}\n".format(ERRCOUNT_GOOGLE)
        else:
            status = 'УСПЕХ'
            strMess = "Выполнение скрипта завершено успешно. \n\n" \
                      + "Ошибок Google: {}\n".format(ERRCOUNT_GOOGLE) \
                      + "Ошибок doTERRA: {}\n".format(ERRCOUNT_GOOGLE) \
                      + "Ошибок BAIKAL: {}\n".format(ERRCOUNT_GOOGLE)

        msg = EmailMessage()
        msg.set_content(strDate + '\n' + strMess)
        msg['Subject'] = f'[{status}] - Parser + GSheets + Baikal ({strDate})'
        msg['From'] = fromaddr
        msg['To'] = toaddr

        s = smtplib.SMTP_SSL(_smtp_server, _smtp_port)
        s.login(fromaddr, frompass)
        s.send_message(msg)
        s.quit()
        EMAIL_SENT = True


# Управление аккаунтами Baikal
def manage_baikal_account(config, user, pwd, dispname="Аноним", upd_pwd=False):
    global ERRCOUNT_BAIKAL
    global STUCK_AT_BAIKAL
    # SQL-запросы
    add_user = ("INSERT INTO users "
                "(username, digesta1) "
                "VALUES (%(username)s, %(digesta1)s)")

    add_principal = ("INSERT INTO principals "
                     "(uri, email, displayname) "
                     "VALUES (%(uri)s, %(email)s, %(displayname)s)")

    add_addressbook = ("INSERT INTO addressbooks "
                       "(principaluri, displayname, uri, description, synctoken) "
                       "VALUES (%(principaluri)s, %(displayname)s, %(uri)s, %(description)s, %(synctoken)s)")

    check_user = ("SELECT * FROM users "
                  "WHERE username = %s")
    check_principal = ("SELECT * FROM principals "
                       "WHERE uri = %s")
    check_addressbook = ("SELECT * FROM addressbooks "
                         "WHERE principaluri = %s AND uri = %s")

    update_user = ("UPDATE users "
                   "SET digesta1=%(digesta1)s "
                   "WHERE username=%(username)s")

    # Данные для запроса
    USER = user
    REALM = 'BaikalDAV'
    PASS = pwd

    user_new = {
        "username": USER,
        "digesta1": hashlib.md5(str(USER + ":" + REALM + ":" + PASS).encode('ascii')).hexdigest()
    }
    principal_new = {
        "uri": "principals/" + USER,
        "email": USER + "@bediamond.ru",
        "displayname": dispname
    }
    addressbook_new = {
        "principaluri": "principals/" + USER,
        "displayname": "Контакты",
        "uri": "default",
        "description": "Адресная книга лидера " + dispname,
        "synctoken": 1
    }

    # Для обновления существующих записей
    user_existing = [USER]
    principal_existing = ["principals/" + USER]
    addressbook_existing = ["principals/" + USER, "default"]

    # Подключение к MySQL
    try:
        cnx = mysql.connector.connect(user=config['mysql_user'],
                                      password=config['mysql_pwd'],
                                      host=config['mysql_host'],
                                      database=config['mysql_db'])
        cursor = cnx.cursor()

        # Проверка базы на наличие аккаунта
        cursor.execute(check_user, user_existing)
        USER_FLAG = len(cursor.fetchall())
        cursor.execute(check_principal, principal_existing)
        PRIN_FLAG = len(cursor.fetchall())
        cursor.execute(check_addressbook, addressbook_existing)
        ADDR_FLAG = len(cursor.fetchall())

        # Добавление записи в БД
        if USER_FLAG != 1:
            cursor.execute(add_user, user_new)
        if PRIN_FLAG != 1:
            cursor.execute(add_principal, principal_new)
        if ADDR_FLAG != 1:
            cursor.execute(add_addressbook, addressbook_new)

        if not USER_FLAG or not PRIN_FLAG or not ADDR_FLAG:
            cnx.commit()
            print_l('Аккаунт ' + USER + ' создан/восстановлен.')
        # Если запись есть в БД, но нет данных в таблице, то заменяется пароль
        elif upd_pwd:
            cursor.execute(update_user, user_new)
            cnx.commit()
            print_l('Пароль аккаунта ' + USER + ' обновлен.')

    except mysql.connector.Error as err:

        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            # print("Неправильный логин/пароль")
            ERRCOUNT_BAIKAL += 1
            ERRSTACK.append(
                [
                    f'Baikal - Авторизация (Уровень {LEVEL}, ИД = {USER})',
                    f'Неправильный логин/пароль',
                    traceback.format_exc()
                ]
            )
        # raise ValueError('Ошибка Baikal: Неправильный логин/пароль')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            ERRCOUNT_BAIKAL += 1
            ERRSTACK.append(
                [
                    f'Baikal - Авторизация (Уровень {LEVEL}, ИД = {USER})',
                    f'БД не существует',
                    traceback.format_exc()
                ]
            )
        # raise ValueError('БД не существует!')
        else:
            ERRCOUNT_BAIKAL += 1
            STUCK_AT_BAIKAL = 1
            ERRSTACK.append(
                [
                    f'Baikal - БД (Уровень {LEVEL}, ИД = {USER})',
                    str(err),
                    traceback.format_exc()
                ]
            )
    # raise ValueError(str(err))
    finally:
        cursor.close()
        cnx.close()


# по каждому пользователю в Salebot по API.
def send_SaleBot(salebot_url, client_id, people_count):
    try:
        payload = {"client_id": client_id, "variables": {"клиент.Команда": people_count}}
        r = requests.post(salebot_url, json=payload)
    except:
        pass


# Создание конфигурации .mobileconfig
def get_mobileconfig(bname, bpass, dtname=None):
    mcTemp = etree.parse(os.path.join(os.path.dirname(__file__), 'baikal.mobileconfig'))
    root = mcTemp.getroot()
    elList = {n: element for n, element in enumerate(root.iter())}
    params = {elList[i].text: elList[i + 1] for i in range(len(elList)) if (elList[i].tag == 'key')}
    # SYSTEM PayloadIdentifier
    elList[9].text = str(dtname) if dtname is not None else 'com.baikal.carddav'
    # LOCAL
    params['PayloadIdentifier'].text = str(dtname) if dtname is not None else 'com.baikal.carddav'
    params['CardDAVAccountDescription'].text = str(dtname) if dtname is not None else 'A Carddav Description'
    params['CardDAVPrincipalURL'].text += str(bname) + '/'
    params['CardDAVUsername'].text = str(bname)
    params['CardDAVPassword'].text = str(bpass).replace('&', '&amp;')

    return io.BytesIO(etree.tostring(mcTemp, xml_declaration=True, encoding='utf-8'))


# Загрузка таблицы Google
def load_google_sheet(gcli, gs_key, core=False):
    global ERRCOUNT_GOOGLE
    global STUCK_AT_GOOGLE
    try:
        def sheet_status(label):
            print_l(label.upper() + ' - ' + ('ЕСТЬ' if label in res else 'ОТСУТСТВУЕТ'))
            if label not in res and label != LDNAME:
                print_l('Восстанавливаем таблицу ' + label + '...')
                sh.add_worksheet(title=label)

        print_l('Открываем таблицы CRM...')
        sh = gcli.open_by_key(gs_key)
        res = {sh.sheet1.title: sh.sheet1}

        if not core:
            print_l('ИМЯ ТАБЛИЦЫ: ' + sh.title)
            # {'название_таблицы': сама таблица}
            res = {item.title: item for item in sh.worksheets()}
            print_l('Проверяем наличие страниц...')
            for i in WKSHEETS:
                sheet_status(i)
            # Дублируем для принятия изменений
            sh = gcli.open_by_key(gs_key)
            res = {item.title: item for item in sh.worksheets()}
        else:
            print_l('Открыта корневая таблица.')

        return sh, res
    except:
        ERRCOUNT_GOOGLE += 1
        STUCK_AT_GOOGLE = 1
        ERRSTACK.append(
            [
                f'Google - Открытие таблицы (Уровень {LEVEL})',
                f'Невозможно открыть Google Таблицу (ключ = {gs_key})',
                traceback.format_exc()
            ]
        )
        print('===== [#ERROR] Ошибка при подключении к таблице Google =====')
        raise ValueError


# Скачивание БД из личного кабинета doTERRA
def get_doterra_db(dtuser, passwd):
    global ERRCOUNT_DOTERRA
    global STUCK_AT_DOTERRA
    # Предварительные настройки браузера
    options = Options()
    options.headless = True
    options.binary_location = '/usr/bin/firefox'

    serv = Service('www/geckodriver')
    driver = webdriver.Firefox(service=serv, options=options)
    driver.implicitly_wait(90)  # seconds

    cache_filepath = f"{CACHE_DIRPATH}/pages_data_{dtuser}.json"

    def process_tab1(driver: webdriver.Firefox):
        driver.find_element(By.CSS_SELECTOR, "#DETAIL_FOCUSID").clear()
        driver.find_element(By.CSS_SELECTOR, "#DETAIL_FOCUSID").send_keys(dtuser)

        driver.find_element(By.CSS_SELECTOR, "div.levels:nth-child(1) > div:nth-child(2) > span:nth-child(2)").click()
        WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)")))
        driver.find_element(By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)").click()

        driver.find_element(By.NAME, "DETAIL_END_LEVEL").clear()
        driver.find_element(By.NAME, "DETAIL_END_LEVEL").send_keys("30")
        # driver.save_full_page_screenshot('button.png')
        try:
            driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Close"]').click()
        except:
            pass
        # driver.save_full_page_screenshot('button-before.png')
        driver.find_element(By.CSS_SELECTOR,
                            "div.four:nth-child(3) > div:nth-child(1) > div:nth-child(2) > span:nth-child(2)").click()
        WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)")))
        driver.find_element(By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)").click()

        button = driver.find_element(By.CSS_SELECTOR,
                                     "div.sixteen:nth-child(4) > div:nth-child(1) > div:nth-child(2) > div:nth-child(3)")
        if button.text != "Вся Структура":
            button.click()
            try:
                WebDriverWait(driver, 90).until(EC.element_to_be_clickable((By.XPATH,
                                                                            "/html/body/div[2]/div/div/div[1]/div[1]/form/div[3]/div/div/div[2]/section[1]/div/div/fieldset/div/div/div[4]/div/div/div[2]/div[1]")))  # текущая верстка
            except:
                WebDriverWait(driver, 90).until(EC.element_to_be_clickable((By.XPATH,
                                                                            "/html/body/div[2]/div/div/div[1]/div[1]/form/div[2]/div/div/div[2]/section[1]/div/div/fieldset/div/div/div[4]/div/div/div[2]/div[1]")))  # старая верстка
            driver.find_element(By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)").click()

    def load_cached_pages_data():
        try:
            with open(cache_filepath, "r") as f:
                return json.load(f)

        except:
            return {}

    def save_cached_pages_data(data):
        os.makedirs(CACHE_DIRPATH, exist_ok=True)

        with open(f"{CACHE_DIRPATH}/pages_data_{dtuser}.json", "w") as f:
            json.dump(data, f)

    # { pageIndex: htmlTable }
    pages_data = load_cached_pages_data()

    try:
        print_l('===== ВЕБ-СКРАПИНГ =====')

        print_l('Загрузка страницы через Firefox...')
        driver.set_page_load_timeout(30)

        loc_conn = 0
        loc_tries = 1

        while loc_conn == 0:
            try:
                print_l('Попытка соединения ' + str(loc_tries))
                driver.get(_dt['dt_lk_url'])
                time.sleep(3)
                loc_conn = 1
            except:
                # print(traceback.format_exc())
                loc_tries += 1
                if loc_tries > 5:
                    raise ValueError('Превышено число попыток (5) на подключение.')

        print_l('Ожидаем загрузки панели входа...')
        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'form-field-text'))
        )

        print_l('Ввод данных для входа в аккаунт...')
        txtLogin = driver.find_element(By.CLASS_NAME, 'form-field-text')
        txtPass = driver.find_element(By.CLASS_NAME, 'form-field-password')

        txtLogin.send_keys(dtuser)
        txtPass.send_keys(passwd)

        txtPass.send_keys(Keys.RETURN)

        print_l('Ожидаем завершения авторизации...')
        theTable = 'null'

        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "myaccountmenu"))
            )
        except TimeoutException:
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "account-avatar"))
                )
            except TimeoutException:
                driver.save_full_page_screenshot("fpsckrin.png")
                pass

        driver.save_full_page_screenshot("fpsckrin.png")

        print_l('Заходим в личный кабинет за отчетом...')
        # driver.get(_dt["dt_lk_url"])
        loc_conn = 0
        loc_tries = 1

        while loc_conn == 0:
            try:
                print_l('Попытка соединения ' + str(loc_tries))
                driver.get(_dt['dt_lk_url'])
                time.sleep(3)
                loc_conn = 1
            except:
                # print(traceback.format_exc())
                loc_tries += 1
                if loc_tries > 5:
                    raise ValueError('Превышено число попыток (5) на подключение.')

        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, "myaccountpopup_new"))  # старое значение "mydetaildata"
        )

        print_l('Меняем язык интерфейса на русский...')

        hover = WebDriverWait(driver, 90).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".myaccountmenu")))
        ActionChains(driver).move_to_element(hover).perform()

        WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.ID, "selectlanguage"))
        ).click()
        a = driver.find_element(By.CSS_SELECTOR, "div.fluid:nth-child(3)")
        a = a.find_elements(By.TAG_NAME, 'div')
        languages = []
        for i in a:
            languages.append(i.get_attribute("data-value"))

        if "ru" in languages:
            language = "ru"
        elif "en_dot" in languages:
            language = "en_dot"
        elif "en_uk" in languages:
            language = "en_uk"
        elif "language_en" in languages:
            language = "language_en"

        WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f'#selectlanguage .ui.fluid.menu .item[data-value="{language}"]'))
        ).click()

        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'#selectlanguage .ui.fluid.menu .item.selected.active[data-value="{language}"]'))
        )

        print_l("Устанавливаем свои настройки...")

        process_tab1(driver)

        driver.find_element(By.ID, "tab2").click()

        button = driver.find_element(By.CSS_SELECTOR,
                                     "div.options-columns__item:nth-child(1) > label:nth-child(1) > span:nth-child(3)")
        if button.value_of_css_property("background-color")[4] != "5":
            button.click()
            button.click()
        else:
            button.click()

        driver.find_element(By.CSS_SELECTOR, "#tab2-tab > div > div > fieldset > div > div:nth-child(25)").click()
        time.sleep(2)
        try:
            driver.find_element(By.XPATH,
                                "/html/body/div[2]/div/div/div[1]/div[1]/form/div[3]/div/div/div[2]/section[2]/div/div/div/div/button[2]").click()  # текущая верстка
        except:
            driver.find_element(By.XPATH,
                                "/html/body/div[2]/div/div/div[1]/div[1]/form/div[2]/div/div/div[2]/section[2]/div/div/div/div/button[2]").click()  # старая верстка

        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, "AjaxTableDiv")))  # старое значение "mydetaildata"

        elPages_email = driver.find_elements(By.NAME, 'StartNum')

        time.sleep(1)

        process_tab1(driver)

        driver.find_element(By.ID, "tab2").click()

        button = driver.find_element(By.CSS_SELECTOR,
                                     "div.options-columns__item:nth-child(1) > label:nth-child(1) > span:nth-child(3)")
        if button.value_of_css_property("background-color")[4] != "5":
            button.click()

        time.sleep(1)
        driver.find_element(By.ID, "tab3").click()

        for i in range(1, 3):
            button = driver.find_element(By.CSS_SELECTOR,
                                         f"fieldset.field:nth-child({i}) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > label:nth-child(1) > span:nth-child(2)")
            if button.value_of_css_property("background-color")[4] != "5":
                button.click()

        button = driver.find_element(By.CSS_SELECTOR,
                                     "div.inline:nth-child(2) > div:nth-child(2) > div:nth-child(1) > label:nth-child(1) > span:nth-child(2)")
        if button.value_of_css_property("background-color")[4] != "5":
            button.click()

        button = driver.find_element(By.CSS_SELECTOR,
                                     "div.options-columns__item:nth-child(2) > label:nth-child(1) > span:nth-child(3)")
        if button.value_of_css_property("background-color")[4] != "5":
            button.click()

        driver.find_element(By.CSS_SELECTOR, "div.field:nth-child(4) > div:nth-child(2) > span:nth-child(2)").click()
        WebDriverWait(driver, 90).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1) > span:nth-child(1)")))
        driver.find_element(By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1) > span:nth-child(1)").click()

        a = driver.find_element(By.CSS_SELECTOR,
                                "div.eight:nth-child(3) > fieldset:nth-child(3) > div:nth-child(2) > div:nth-child(2) > span:nth-child(2)")
        driver.execute_script('arguments[0].click();', a)
        WebDriverWait(driver, 90).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)")))
        a = driver.find_element(By.CSS_SELECTOR, "div.visible:nth-child(4) > div:nth-child(1)")
        driver.execute_script('arguments[0].click();', a)

        print_l('Обновляем отчет...')
        time.sleep(2)
        WebDriverWait(driver, 90).until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                    "#tab3-tab > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > button:nth-child(2)")))
        a = driver.find_element(By.CSS_SELECTOR,
                                '#tab3-tab > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > button:nth-child(2)')
        driver.execute_script(
            'document.getElementsByClassName("adaptive-tabs__button adaptive-tabs__button--submit ui button primary small")[2].click();',
            a)

        WebDriverWait(driver, 90).until(
            EC.presence_of_element_located((By.ID, "AjaxTableDiv")))  # старое значение "mydetaildata"

        print_l('Проверяем, сколько страниц нужно вытащить...')
        elPages = driver.find_elements(By.NAME, 'StartNum')
        if len(elPages) > 0:
            print_l('Есть несколько страниц с данными!')
            selectPages = Select(elPages[0])
            pageCount = len(selectPages.options)
            print_l('Снимаем данные с каждой страницы...')
            for page_index in range(pageCount):
                print_l('----- Страница ' + str(page_index + 1) + ' из ' + str(pageCount))

                cache_key = str(page_index)
                if cache_key in pages_data:
                    print_l(f'Страница {page_index + 1} найдена в кэше')
                    continue

                curSelect = Select(driver.find_elements(By.NAME, 'StartNum')[0])
                curSelect.select_by_index(page_index)

                WebDriverWait(driver, 90).until(
                    EC.presence_of_element_located((By.ID, "TableArea")))  # старое значение "mydetaildata"
                driver.implicitly_wait(3)
                soup_table = BeautifulSoup(driver.page_source, 'html.parser').find(
                    id='TableArea')  # старое значение "mydetaildata"
                soup_table.find(id='SearchHeader').decompose()  # старое значение SearchHeader

                html_table = str(soup_table)

                pages_data[cache_key] = html_table

        # with open('doterra_multi_'+str(p+1)+'.html', 'w') as bowl:
        #    bowl.write(str(soup[p]))
        else:
            print_l('В наличии только 1 страница. Извлекаем её...')
            soup_table = BeautifulSoup(driver.page_source, 'html.parser').find(
                id='TableArea')  # старое значение "mydetaildata"
            soup_table.find(id='SearchHeader').decompose()  # старое значение SearchHeader

            pages_data["1"] = str(soup_table)

        # Преобразовываем словарь в упорядоченный список по номеру страницы
        html_tables = [
            value
            for _, value in sorted(
                pages_data.items(),
                key=lambda item: int(item[0])
            )
        ]

        # Очищаем кэш так как все данные получены
        save_cached_pages_data({})

        return html_tables, language

    except:
        # В случае ошибки сохраняем прогресс для использования при следующем запуске
        save_cached_pages_data(pages_data)

        ERRCOUNT_DOTERRA += 1
        STUCK_AT_DOTERRA = 1
        ERRSTACK.append(
            [
                f'doTERRA - Загрузка данных (Уровень {LEVEL})',
                f'Невозможно получить доступ к личному кабинету doTERRA (ИД = {dtuser}).',
                traceback.format_exc()
            ]
        )
        driver.quit()
        print('===== [#ERROR] Ошибка при подключении к doTERRA =====')
        raise ValueError

    finally:
        driver.quit()


# Парсинг данных doTERRA
def parse_doterra_db(bsoup, gcli, lurl='', language: str = None, file=True):
    global ERRCOUNT_DOTERRA
    global STUCK_AT_DOTERRA

    translate_dict = dict()
    # print([language])
    if language == "en_dot":
        translate_dict = {"Watch List": "СПИСОК ПРОСМОТРОВ", "Member ID": "ID Пользователя", "Name": "Имя",
                          "Member Type": "Тип пользователя",
                          "Levels": "Уровни", "Current Rank": "Текущий ранг", "Highest Rank": "Наивысший ранг",
                          "Next LRP PV": "PV от следующего заказа LRP",
                          "Next LRP Date": "Дата следующего LRP", "Last Order Date": "Дата последнего заказа",
                          "Enrollment Date": "Дата подписания",
                          "Sponsor ID": "ID Спонсора", "Sponsor Name": "Имя Спонсора", "Enroller ID": "ID Рекрутера",
                          "Enroller Name": "Имя Рекрутера",
                          "Home Phone": "Телефон", "Cell Phone": "Cell", "Work Phone": "Work", "Address 1": "Адрес",
                          "Address 2": "address_2", "Email:": "Email",
                          "City": "Город", "State": "Регион/Область", "Postal Code": "Почтвый индекс",
                          "Region": "Страна:", "May 2023": "Май 2023", "April 2023":
                              "Апрель 2023", "March 2023": "Март 2023", "February 2023": "февраль 2023",
                          "January 2023": "январь 2023"}
    elif language == "en_uk":
        translate_dict = {"WATCH LIST": "СПИСОК ПРОСМОТРОВ", "Member ID": "ID Пользователя", "Name": "Имя",
                          "Member Type": "Тип пользователя",
                          "Levels": "Уровни", "Current Rank": "Текущий ранг", "Highest Rank": "Наивысший ранг",
                          "Next LRP PV": "PV от следующего заказа LRP",
                          "Next LRP Date": "Дата следующего LRP", "Last Order Date": "Дата последнего заказа",
                          "Enrollment Date": "Дата подписания",
                          "Sponsor ID": "ID Спонсора", "Sponsor Name": "Имя Спонсора", "Enroller ID": "ID Рекрутера",
                          "Enroller Name": "Имя Рекрутера",
                          "Home Phone": "Телефон", "Cell Phone": "Cell", "Work Phone": "Work", "Address": "Адрес",
                          "address_2": "address_2", "Email:": "Email",
                          "City": "Город", "County or Province": "Регион/Область", "Postal Code": "Почтвый индекс",
                          "Country": "Страна:", "April 2023":
                              "Апрель 2023", "March 2023": "Март 2023", "February 2023": "февраль 2023",
                          "January 2023": "январь 2023", "December 2022":
                              "Декабрь 2022", "November 2022": "Ноябрь 2022"}

    def fixMonth(x):
        for key, value in months.items():
            if key in x.lower():
                res = x.lower().replace(key, value)
                return res
        return x

    def readHtmlTable(html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Убираем из html всё ненужное
        for n in soup.select("style, script, img, video, svg"):
            n.decompose()

        html = str(soup)

        return pd.read_html(html, flavor='bs4', parse_dates=True, na_values='', keep_default_na=False)[0]

    def dateReorder(x):
        def dropPV(xx):
            for ae in ['OV', 'PV', 'LRP PV']:
                if ae in xx:
                    return xx.replace(ae + ' ', '')
            return xx

        colSource = x.columns
        colDates = colSource.map(
            lambda x: pd.to_datetime(
                dropPV(x), errors='coerce', format='%m.%y'
            )).dropna().unique().sort_values(ascending=False)

        localOrder = []
        for i in colDates:
            for o in ['OV', 'PV', 'LRP PV']:
                localOrder.append(i.strftime(o + ' %m.%y'))

        c = x.drop(localOrder, axis=1)
        d = x[localOrder]
        # c['PV от следующего заказа LRP'] = c['PV от следующего заказа LRP'].apply(lambda mc: locale.atof(str(mc)))
        d = x[localOrder].applymap(lambda mc: locale.atof(str(mc).replace('^', '')))
        res = pd.concat([c, d], axis=1)
        return res

    try:
        print_l('===== ПАРСИНГ ТАБЛИЦЫ =====')

        print_l('Собираем таблицы в одну...')
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_colwidth', None)
        dfParts = []
        for tableAreaNode in bsoup:
            dfParts.append(
                readHtmlTable(tableAreaNode)
            )

        # for i in dfParts:
        #	print(i)
        dfIn = pd.concat(dfParts, ignore_index=True)
        # print(dfIn.columns)
        dfIn = dfIn.rename(columns=translate_dict)
        try:
            dfIn = dfIn.drop('СПИСОК ПРОСМОТРОВ', axis=1, level=0)
        except:
            if language == "en_dot":
                translate_dict = {"WatchList": "СПИСОК ПРОСМОТРОВ", "MemberID": "ID Пользователя", "Name": "Имя",
                                  "MemberType": "Тип пользователя",
                                  "Levels": "Уровни", "Current Rank": "Текущий ранг", "Highest Rank": "Наивысший ранг",
                                  "NextLRP PV": "PV от следующего заказа LRP",
                                  "NextLRP Date": "Дата следующего LRP", "LastOrder Date": "Дата последнего заказа",
                                  "EnrollmentDate": "Дата подписания",
                                  "SponsorID": "ID Спонсора", "Sponsor Name": "Имя Спонсора",
                                  "Enroller ID": "ID Рекрутера", "Enroller Name": "Имя Рекрутера",
                                  "Home Phone": "Телефон", "Cell Phone": "Cell", "Work Phone": "Work",
                                  "Address 1": "Адрес", "Address 2": "address_2", "Email:": "Email",
                                  "City": "Город", "State": "Регион/Область", "Postal Code": "Почтвый индекс",
                                  "Region": "Страна:", "May 2023": "Май 2023",
                                  "April 2023": "Апрель 2023", "March 2023": "Март 2023",
                                  "February 2023": "февраль 2023", "January 2023": "январь 2023"}
                dfIn = dfIn.rename(columns=translate_dict)
                dfIn = dfIn.drop('СПИСОК ПРОСМОТРОВ', axis=1, level=0)
        print(dfIn.columns)
        print_l('Удаляем записи с пустыми и нечисловыми ID (если есть)...')
        nullInd = dfIn["ID Пользователя"].loc[dfIn["ID Пользователя"].isnull()["ID Пользователя"]].index
        dfIn.drop(nullInd, inplace=True)
        nanInd = dfIn["ID Пользователя"].loc[
            pd.to_numeric(dfIn["ID Пользователя"]["ID Пользователя"], errors='coerce').isnull()].index
        dfIn.drop(nanInd, inplace=True)
        dfIn["ID Пользователя"] = dfIn["ID Пользователя"].astype(int)
        dfIn["ID Спонсора"] = dfIn["ID Спонсора"].astype(int)
        dfIn["ID Рекрутера"] = dfIn["ID Рекрутера"].astype(int)
        dfIn["Уровни"] = dfIn["Уровни"].fillna(0).astype(int)
        print_l('Обрабатываем столбцы...')
        dfIn.rename(columns={"ID Пользователя": "ID",
                             "Имя": "Фамилия",
                             "Тип пользователя": "Тип"}, inplace=True)
        dfIn.insert(2, "Имя", pd.Series(dtype='object'), allow_duplicates=True)

        months = {'январь': 'январь',
                  'февраль': 'февраль',
                  'март': 'март',
                  'апрель': 'апрель',
                  'май': 'май',
                  'июнь': 'июнь',
                  'июль': 'июль',
                  'август': 'август',
                  'сентябрь': 'сентябрь',
                  'октябрь': 'октябрь',
                  'ноябрь': 'ноябрь',
                  'декабрь': 'декабрь',
                  'января': 'январь',
                  'февраля': 'февраль',
                  'марта': 'март',
                  'апреля': 'апрель',
                  'мая': 'май',
                  'июня': 'июнь',
                  'июля': 'июль',
                  'августа': 'август',
                  'сентября': 'сентябрь',
                  'октября': 'октябрь',
                  'ноября': 'ноябрь',
                  'декабря': 'декабрь',
                  'january': 'январь',
                  'february': 'февраль',
                  'march': 'март',
                  'april': 'апрель',
                  'may': 'май',
                  'june': 'июнь',
                  'july': 'июль',
                  'august': 'август',
                  'september': 'сентябрь',
                  'october': 'октябрь',
                  'november': 'ноябрь',
                  'december': 'декабрь'}

        pvSource = dfIn.columns.get_level_values(0)
        pvDT = pvSource.map(lambda x: pd.to_datetime(fixMonth(x), errors='coerce', format='%B %Y'))
        pvTarget = pd.Series(pvSource)

        pvRenamer = pd.Series(dfIn.columns.get_level_values(1)) + ' ' + pd.Series(
            pvDT.map(lambda x: x.strftime('%m.%y')))
        pvTarget.loc[pvRenamer.notnull()] = pvRenamer.loc[pvRenamer.notnull()]

        dfMid = dfIn.droplevel(level=1, axis=1)
        dfMid.set_axis(pvTarget, axis=1, inplace=True)

        # Сортировка столбцов с датами
        pvMarks = ['OV', 'PV', 'LRP PV']
        pvDates = pvDT.dropna().unique().sort_values(ascending=False)

        trueOrder = []
        for i in pvDates:
            for o in pvMarks:
                trueOrder.append(i.strftime(o + ' %m.%y'))

        dfCorePart = dfMid.drop(trueOrder, axis=1)
        dfCorePart['PV от следующего заказа LRP'] = dfCorePart['PV от следующего заказа LRP'].apply(
            lambda mc: locale.atof(str(mc)))
        dfDatePart = dfMid[trueOrder]
        dfMid = pd.concat([dfCorePart, dfDatePart], axis=1)

        print_l('Обрабатываем колонки...')
        oldNames = dfMid['Фамилия']

        # Splitting Name column
        def nameSplit(x, side=0):
            if str(x) == 'nan':
                return ''

            nameSlice = str(x).split(', ')
            if len(nameSlice) == 1:
                name1 = nameSlice[0].split(' ', maxsplit=1)[0]
                if len(nameSlice[0].split(' ', maxsplit=1)) == 1:
                    name2 = ''
                else:
                    name2 = nameSlice[0].split(' ', maxsplit=1)[1]
                    # Убираем отчество из имени
                    name2 = name2.split(' ', maxsplit=1)[0]
            else:
                name1 = nameSlice[0]
                name2 = nameSlice[1].split(' ', maxsplit=1)[0]

            if side == 0:
                return name1
            elif side == 1:
                return name2
            else:
                return ''

        dfMid['Имя'] = oldNames.apply(nameSplit, side=1)
        dfMid['Фамилия'] = oldNames.apply(nameSplit, side=0)

        def format_date(x):
            try:
                if language == "ru":
                    return str(x).replace('/', '.')
                else:
                    a = list(str(x))
                    if len(a) == 10:
                        a[0:2], a[3:5] = a[3:5], a[0:2]
                    elif len(a) == 9:
                        a[0], a[2:4] = a[2:4], a[0]
                    return "".join(chain.from_iterable(a)).replace("/", ".")
            except Exception as e:
                return x

        # Re-formatting dates (8,9,10)
        dfMid[['Дата следующего LRP',
               'Дата последнего заказа',
               'Дата подписания']] = dfMid[['Дата следующего LRP',
                                            'Дата последнего заказа',
                                            'Дата подписания']].applymap(
            format_date, na_action='ignore')

        # Re-formatting phone numbers (15,16,17)
        def restorePhoneFormat(x):
            cellRows = [col for col in x.columns if 'Телефон' in col
                        or 'Cell' in col
                        or 'Work' in col]
            if cellRows != []:
                x[cellRows] = x[cellRows].applymap(lambda x: '\'+' + str(x).replace('-', ''),
                                                   na_action='ignore').replace('\.0', '', regex=True).fillna('\'+')
                x[cellRows] = x[cellRows].applymap(lambda y: '' if y == '\'+' else y)

        restorePhoneFormat(dfMid)

        dfMid[['Имя Спонсора', 'Имя Рекрутера']] = dfMid[['Имя Спонсора', 'Имя Рекрутера']].applymap(
            lambda x: x.replace(', ', ' ') if type(x) is not float else x)

        adressesToSplit = dfMid['address_2']

        def regionSplit(x, side=0):
            if str(x) == 'nan':
                return ''

            nameSlice = str(x).split(', ')
            if len(nameSlice) == 1:
                name1 = nameSlice[0].split(' ', maxsplit=1)[0]
                if len(nameSlice[0].split(' ', maxsplit=1)) == 1:
                    name2 = ''
                else:
                    name2 = nameSlice[0].split(' ', maxsplit=1)[1]
            else:
                name1 = nameSlice[0]
                name2 = nameSlice[1]

            if side == 0:
                return name1
            elif side == 1:
                return name2
            else:
                return ''

        dfMid['Город'] = adressesToSplit.apply(regionSplit, side=0)
        dfMid['Регион/Область'] = adressesToSplit.apply(regionSplit, side=1).apply(
            lambda x: x.replace('Москва', 'Московская'))

        # ===== ===== ===== ===== =====

        if not pd.isna(lurl) and file:
            sh, shList = load_google_sheet(gcli, lurl.split('/')[5])
            wkTeam = shList['Команда']
            wkLost = shList['Команда Архив']
            wkArchive = shList['PV Архив']
            wkUpdates = shList['Изменения']

            dfTeam = wkTeam.get_as_df(empty_value=np.nan)
            dfLost = wkLost.get_as_df(empty_value=np.nan)
            dfArchive = wkArchive.get_as_df(empty_value=np.nan)

        # dfUpdates = wkUpdates.get_as_df(empty_value=np.nan)
        else:
            sh = None
            shList = None
            dfTeam = dfMid.copy()
            dfLost = pd.DataFrame()
            dfArchive = pd.DataFrame()
        # ===== ===== ===== ===== =====

        # dfArchive check
        if dfArchive.empty:
            print_l("Пустая таблица Архив PV! Восстанавливаем заголовки (по донору)...")
            wkArchive.clear()
            wkArchive.update_row(1, ['ID'])
            wkArchive.refresh(update_grid=True)
            dfArchive = wkArchive.get_as_df(empty_value=np.nan)
        # dfTeam check
        if dfTeam.empty:
            print_l("Пустая таблица Команда! Восстанавливаем заголовки (по донору)...")
            wkTeam.clear()
            wkTeam.update_row(1, list(dfMid.reset_index().columns.values))
            wkTeam.refresh(update_grid=True)
            dfTeam = wkTeam.get_as_df(empty_value=np.nan)
        dfTeam = dateReorder(dfTeam)
        dfTeam['PV от следующего заказа LRP'] = dfTeam['PV от следующего заказа LRP'].apply(
            lambda mc: locale.atof(str(mc)))

        restorePhoneFormat(dfTeam)
        restorePhoneFormat(dfLost)

        dfTeamI = dfTeam.set_index('ID')
        dfMidI = dfMid.set_index('ID')

        print_l('Проверяем целостность ID...')
        print_l('---Присутствующие в доноре и исходнике:')
        print_l(dfTeamI.index[dfTeamI.index.isin(dfMidI.index)].values)
        print_l('---Отсутствуют в доноре:')
        print_l(dfTeamI.index[~dfTeamI.index.isin(dfMidI.index)].values)
        print_l('---Продублированы:')
        print_l(dfTeamI.index[dfTeamI.index.duplicated()].values)
        print_l('---Новые:')
        print_l(dfMidI.index[~dfMidI.index.isin(dfTeamI.index)].values)

        print_l('Убираем дубликаты (при наличии)...')
        dfTeamI = dfTeamI[~dfTeamI.index.duplicated(keep='last')]

        print_l('Переносим отсутствующие ID (при наличии)...')
        if not pd.isna(lurl) and file:
            dfLostNew = dfTeamI.loc[dfTeamI.index[~dfTeamI.index.isin(dfMidI.index)].values]
            pd.concat([dfLostNew])
            dfLostNew = pd.concat([dfLostNew.reset_index(), dfArchive]).set_index('ID')
            dfLostNew.index.rename('ID', inplace=True)

            dfLostNew.update(dfArchive.set_index('ID'))
            if dfLost.empty:
                dfLost = dfLostNew.copy()
            else:
                dfLost = dfLost.set_index('ID')
                # dfLost.columns = dfLostNew.columns
                dfLost = pd.concat([dfLost, dfLostNew], join='inner')
            dfTeamI.drop(dfTeamI.index[~dfTeamI.index.isin(dfMidI.index)], inplace=True)

            print_l('Следующие ID были восстановлены:')
            print_l(dfLost.index[dfLost.index.isin(dfMidI.index)].values)
            print_l('Удаляем восстановленные ID из архива...')
            # Добавить назад в PV Архив
            recID = dfLost.index[dfLost.index.isin(dfMidI.index)]
            dfLost.drop(recID, inplace=True)
            dfLost = dateReorder(dfLost)
            dfLost.fillna('', inplace=True)
            dfLost = dfLost[~dfLost.index.duplicated(keep='first')]
        else:
            print_l('Файл отсутствует, архивировать нечего.')
            dfLost = pd.DataFrame()

        print_l('Проверяем целостность столбцов PV/OV/LRP PV...')
        filterPV_N = dfMidI.columns[dfMidI.columns.str.contains('PV|OV')]
        filterPV_O = dfTeamI.columns[dfTeamI.columns.str.contains('PV|OV')]

        print_l('---Совпадающие поля:')
        print_l(filterPV_N[filterPV_N.isin(filterPV_O)].values)
        print_l('---Устаревшие поля:')
        print_l(filterPV_O[~filterPV_O.isin(filterPV_N)].values)
        print_l('---Новые поля:')
        print_l(filterPV_N[~filterPV_N.isin(filterPV_O)].values)

        fAdded = dfMidI[filterPV_N[~filterPV_N.isin(filterPV_O)].values]
        fRemoved = dfTeamI[filterPV_O[~filterPV_O.isin(filterPV_N)].values]
        fUpdated = dfMidI[filterPV_N[filterPV_N.isin(filterPV_O)].values].drop('PV от следующего заказа LRP', axis=1)
        print_l('Добавляем новые поля (если есть)...')
        dfTeamClean = dfTeamI.copy()
        for i in fAdded.columns:
            dfTeamClean.insert(len(dfTeamClean.columns), i, fAdded[i])
        dfTeamClean.drop(fRemoved.columns, axis=1, inplace=True)

        dfTeamClean = dateReorder(dfTeamClean)
        dfTeamClean.fillna('', inplace=True)

        # start @Sergey_Risovaniy
        try:
            cols_to_drop = [col for col in dfTeamClean.columns if col.startswith('Qual ')]
            dfTeamClean = dfTeamClean.drop(columns=cols_to_drop)
        except:
            pass
        # finish @Sergey_Risovaniy

        print_l('Добавляем новые записи...')
        dfToAdd = dfMidI.loc[dfMidI.index[~dfMidI.index.isin(dfTeamClean.index)].values]
        dfEnd = pd.concat([dfTeamClean, dfToAdd], join='inner')

        print_l('Архивируем старые данные по OV/PV (если есть)...')
        if not pd.isna(lurl) and file:
            idxIDs = dfEnd.index.append(dfLost.index).unique()
            idxDates = fUpdated.columns.append(fAdded.columns).append(fRemoved.columns).append(
                dfArchive.set_index('ID').columns).unique()
            dfNewArch = pd.DataFrame(columns=idxDates,
                                     index=idxIDs)
            dfArchive.drop_duplicates(keep='first', inplace=True)
            # Data from donor
            dfNewArch.update(dfArchive.set_index('ID'))
            # Data from recovered IDs
            dfNewArch.update(recID)
            # Then from processed tables
            dfNewArch.update(fUpdated)
            for i in fRemoved.columns:
                dfNewArch.update(fRemoved[i])
            for i in fUpdated.columns:
                if i not in dfNewArch.columns:
                    dfNewArch.insert(len(dfNewArch.columns), i, fUpdated[i])
                else:
                    dfNewArch.update(fUpdated[i])
            dfNewArch = dateReorder(dfNewArch)
            dfNewArch.fillna('', inplace=True)
            dfNewArch = dfNewArch[~dfNewArch.index.duplicated(keep='first')]

            # НОВОЕ - Добавление содержимого PV Архив к Команде
            try:
                dfEnd = dfEnd.reset_index().merge(dfNewArch.reset_index(), how='left').set_index('ID')
                dfEnd.index.rename('ID', inplace=True)
            except:
                pass
        else:
            print_l('URL отсутствует, архивировать нечего.')
            dfNewArch = pd.DataFrame()

        print_l('Составляем таблицу изменений...')
        dfUpSource = dfMidI.loc[dfEnd.index[dfEnd.index.isin(dfMidI.index)].values].fillna('')
        dfUpTarget = dfEnd.loc[dfEnd.index[dfEnd.index.isin(dfMidI.index)].values].fillna('')

        # Diff detection
        dfUpdateReport = dfUpSource.isin(dfUpTarget).reset_index()
        dfUpdateReport.iloc[:, 1:] = ~dfUpdateReport.iloc[:, 1:]

        # Updating old table
        dfUpdated = dfUpTarget.copy()
        dfUpdated.update(dfUpSource)

        '''
        resulting dataframes
        dfUpdated => wkTeam
        dfLost => wkLost
        dfNewArch => wkArchive
        dfUpdateReport => wkUpdates

        uploadPlan = [
            [dfUpdated, wkTeam],
            [dfLost, wkLost],
            [dfNewArch, wkArchive],
            [dfUpdateReport.set_index('ID'), wkUpdates]
        ]
        '''
        dfParsed = {
            WKSHEETS[0]: dfUpdated,
            WKSHEETS[1]: dfLost,
            WKSHEETS[2]: dfNewArch,
            WKSHEETS[3]: dfUpdateReport.set_index('ID')
        }
        qty = len(dfUpdated.index)
        return sh, shList, dfParsed, qty
        print_l('===== ===== ===== ===== =====')
    except:
        ERRCOUNT_DOTERRA += 1
        STUCK_AT_DOTERRA = 1
        ERRSTACK.append(
            [
                f'doTERRA - Парсинг данных (Уровень {LEVEL})',
                f'Невозможно обработать данные, полученные с сайта doTERRA. Таргет = {str(lurl)}',
                traceback.format_exc()
            ]
        )
        print('===== [#ERROR] Ошибка при обработке данных с doTERRA =====')
        raise ValueError


# Псевдопарсинг для демо-режима
def parse_demo(gcli, lurl='', file=True):
    global ERRCOUNT_DOTERRA
    global STUCK_AT_DOTERRA

    def fixMonth(x):
        for key, value in months.items():
            if key in x.lower():
                res = x.lower().replace(key, value)
                return res
        return x

    def dateReorder(x):
        def dropPV(xx):
            for ae in ['OV', 'PV', 'LRP PV']:
                if ae in xx:
                    return xx.replace(ae + ' ', '')
            return xx

        colSource = x.columns
        colDates = colSource.map(
            lambda x: pd.to_datetime(
                dropPV(x), errors='coerce', format='%m.%y'
            )).dropna().unique().sort_values(ascending=False)

        localOrder = []
        for i in colDates:
            for o in ['OV', 'PV', 'LRP PV']:
                localOrder.append(i.strftime(o + ' %m.%y'))

        c = x.drop(localOrder, axis=1)
        d = x[localOrder]
        # c['PV от следующего заказа LRP'] = c['PV от следующего заказа LRP'].apply(lambda mc: locale.atof(str(mc)))
        d = x[localOrder].applymap(lambda mc: locale.atof(str(mc).replace('^', '')))
        res = pd.concat([c, d], axis=1)
        return res

    def restorePhoneFormat(x):
        cellRows = [col for col in x.columns if 'Телефон' in col
                    or 'Cell' in col
                    or 'Work' in col]
        if cellRows != []:
            x[cellRows] = x[cellRows].applymap(lambda x: '\'+' + str(x).replace('-', ''),
                                               na_action='ignore').replace('\.0', '', regex=True).fillna('\'+')
            x[cellRows] = x[cellRows].applymap(lambda y: '' if y == '\'+' else y)

    try:
        # Загрузка по ссылке
        print_l("Пересылаем данные с демо-таблицы...")
        if not pd.isna(lurl) and file:
            sh, shList = load_google_sheet(gcli, lurl.split('/')[5])
            wkTeam = shList['Команда']
            wkLost = shList['Команда Архив']
            wkArchive = shList['PV Архив']
            wkUpdates = shList['Изменения']

            dfTeam = wkTeam.get_as_df(empty_value=np.nan).set_index('ID')
            dfLost = wkLost.get_as_df(empty_value=np.nan).set_index('ID')
            dfArchive = wkArchive.get_as_df(empty_value=np.nan).set_index('ID')
            dfUpdates = wkUpdates.get_as_df(empty_value=np.nan).set_index('ID')

        # dfUpdates = wkUpdates.get_as_df(empty_value=np.nan)
        else:
            sh = None
            shList = None
            dfTeam = pd.DataFrame()
            dfLost = pd.DataFrame()
            dfArchive = pd.DataFrame()
            dfUpdates = pd.DataFrame()

        restorePhoneFormat(dfTeam)

        dfTeamClean = dateReorder(dfTeam)
        dfTeamClean.fillna('', inplace=True)

        qty = len(dfTeamClean.index)

        dfParsed = {
            WKSHEETS[0]: dfTeamClean,
            WKSHEETS[1]: dfLost,
            WKSHEETS[2]: dfArchive,
            WKSHEETS[3]: dfUpdates
        }

        print_l('Данные получены.')
        print_l('===== ===== ===== ===== =====')
        return sh, shList, dfParsed, qty
    except:
        ERRCOUNT_DOTERRA += 1
        STUCK_AT_DOTERRA = 1
        ERRSTACK.append(
            [
                f'doTERRA - Парсинг данных (Уровень {LEVEL})',
                f'Невозможно обработать данные, полученные с демо-таблицы. Таргет = {str(lurl)}',
                traceback.format_exc()
            ]
        )
        print('===== [#ERROR] Ошибка при обработке данных с демо-таблицы =====')
        raise ValueError


# def send_salebot_variables(client_id: int, )

# Выгрузка таблиц в Google
def upload_to_gsheets(sh, df_parsed_in):
    global ERRCOUNT_GOOGLE
    global STUCK_AT_GOOGLE
    try:
        print_l('===== ЗАГРУЗКА В GOOGLE =====')
        BOLD = pygsheets.Cell("A1")
        NON_BOLD = pygsheets.Cell("A1")
        TEXT0 = pygsheets.Cell("A1")

        BOLD.set_text_format('bold', True)
        NON_BOLD.set_text_format('bold', False)
        TEXT0.set_number_format(FormatType('TEXT'))

        print_l('Обновление таблиц Команда, Команда Архив, PV Архив, Уведомления...')
        for wkc in df_parsed_in:
            if not df_parsed_in[wkc].empty:
                cur_sheet = sh.worksheet_by_title(wkc)
                cur_df: pd.DataFrame = df_parsed_in[wkc].fillna('')

                # Удаляем Qual в том числе из существующих данных в таблице
                cur_df.drop(columns=[
                    str(column_label)
                    for column_label in list(cur_df.columns.values)
                    if str(column_label).startswith("Qual ")
                ], inplace=True)

                drange = pygsheets.datarange.DataRange(start='A1', worksheet=cur_sheet)
                drange.clear()
                drange.apply_format(NON_BOLD)

                cur_sheet.rows = cur_df.shape[0] + 1
                cur_sheet.update_row(1, list(cur_df.reset_index().columns.values))
                if not cur_df.empty:
                    cur_sheet.update_row(2, [list(r) for r in cur_df.reset_index().to_numpy()])

                if len(cur_df.columns) > 1:
                    cur_sheet.frozen_cols = 1
                if not cur_df.empty:
                    cur_sheet.frozen_rows = 1
                cur_sheet.adjust_column_width(1, len(cur_df.columns) + 1)
                drange = pygsheets.datarange.DataRange(start='A1', end='1', worksheet=cur_sheet)
                drange.apply_format(BOLD)
        print_l('Таблица успешно загружена на сервер.')
        print_l('===== ===== ===== ===== =====')
    except:
        print('===== [#ERROR] Невозможно загрузить полученные данные в Google Таблицу =====')

        ERRCOUNT_GOOGLE += 1
        STUCK_AT_GOOGLE = 1
        ERRSTACK.append(
            [
                f'Google - Выгрузка данных (Уровень {LEVEL})',
                f'Невозможно загрузить полученные данные в Google Таблицу. Адрес = {str(sh.url)}',
                traceback.format_exc()
            ]
        )
        raise ValueError


# Выгрузка лидерской таблицы в Google
def upload_leaders_to_gsheets(spreadsheet, leaders_df):
    global ERRCOUNT_GOOGLE
    global STUCK_AT_GOOGLE
    try:
        print_l('===== ЗАГРУЗКА ОБНОВЛЕННОЙ ЛИДЕРСКОЙ ТАБЛИЦЫ В GOOGLE =====')
        BOLD = pygsheets.Cell("A1")
        NON_BOLD = pygsheets.Cell("A1")
        TEXT0 = pygsheets.Cell("A1")

        BOLD.set_text_format('bold', True)
        NON_BOLD.set_text_format('bold', False)
        TEXT0.set_number_format(FormatType('TEXT'))

        cur_sheet = spreadsheet.worksheet_by_title(LDNAME)
        cur_df = leaders_df.copy().fillna('')[LD_COLUMNS_ORDER]
        # print('cur_df', cur_df)
        cur_df[_QTY] = cur_df[_QTY].astype(str).replace('\.0', '', regex=True)

        drange = pygsheets.datarange.DataRange(start='A1', worksheet=cur_sheet)
        drange.clear()
        drange.apply_format(NON_BOLD)

        # cur_sheet.rows = cur_df.shape[0]
        cur_sheet.update_row(1, list(cur_df.columns.values))
        if not cur_df.empty:
            cur_sheet.update_row(2, [list(r) for r in cur_df.to_numpy()])

        if len(cur_df.columns) > 1:
            cur_sheet.frozen_cols = 1
        if not cur_df.empty:
            cur_sheet.frozen_rows = 1
        cur_sheet.adjust_column_width(1, len(cur_df.columns) + 1)
        drange = pygsheets.datarange.DataRange(start='A1', end='1', worksheet=cur_sheet)
        drange.apply_format(BOLD)
        print_l('Лидерская таблица успешно загружена на сервер.')
    except:
        print('===== [#ERROR] Ошибка при обновлении лидерской таблицы =====')

        ERRCOUNT_GOOGLE += 1
        STUCK_AT_GOOGLE = 1
        ERRSTACK.append(
            [
                f'doTERRA - Выгрузка лидерской таблицы (Уровень {LEVEL})',
                f'Невозможно загрузить лидерскую таблицу в Google Таблицы. Адрес = {str(spreadsheet.url)}',
                traceback.format_exc()
            ]
        )
        raise ValueError


# Запись контактов в Baikal
def write_to_baikal(buser, bpass, bdata: pd.DataFrame, bprefix='dt', cname=None, cid=None):
    global ERRCOUNT_BAIKAL
    global STUCK_AT_BAIKAL
    try:
        print_l('Подключение к аккаунту Baikal...')
        need_to_update_password = False
        if pd.isna(buser):
            print_l('ВНИМАНИЕ: Аккаунт Baikal не найден! Создаем новый...')
            # Логин
            _user = str(cid).replace('.0', '')
            # Пароль
            _pass = str(generate_random_password(CHARS))
            need_to_update_password = True
        else:
            _user = str(buser).replace('.0', '')
            _pass = str(bpass)
        manage_baikal_account(_msql, _user, _pass, dispname=cname, upd_pwd=need_to_update_password)

        baikal_api = BaikalApi(
            base_url=_bkl['baikal_url'],
            login=_user,
            password=_pass
        )

        # Загрузка лидерской таблицы (???)
        df_contacts: pd.DataFrame = bdata.copy().reset_index()

        contact_vCards, group_vCards = _build_vCards_with_rules(
            df_contacts=df_contacts,
            cfg=_vc,
            prefix=bprefix,
            current_user_id=_user
        )

        print_l('Запись контактов в Baikal...')
        _write_vCards_to_baikal_book(baikal_api, _user, contact_vCards)

        print_l('Запись групп в Baikal...')
        _write_vCards_to_baikal_book(baikal_api, _user, group_vCards)

        return _user, _pass

    except:
        ERRCOUNT_BAIKAL += 1
        STUCK_AT_BAIKAL = 1
        ERRSTACK.append(
            [
                f'Baikal - Запись контактов (Уровень {LEVEL})',
                f'Невозможно загрузить контакты в адресную книгу Baikal (логин = {_user}).',
                traceback.format_exc()
            ]
        )
        print('===== [#ERROR] Ошибка при обновлении лидерской таблицы =====')
        raise ValueError


def _build_vCards_with_rules(df_contacts: pd.DataFrame, cfg: dict, prefix: str, current_user_id: str):
    contact_vCards = []
    group_vCards = []
    member_uids_by_rule = {}

    for _, contact_tbl in df_contacts.iterrows():
        matched_vcard_rules = vcard_utils.VCardUtils.get_matched_rules(contact_tbl, cfg, current_user_id)

        contact_uid, contact_vCard_text = vcard_utils.VCardUtils.build_contact(
            tbl=contact_tbl,
            cfg=cfg,
            pref=prefix,
            matched_rules=matched_vcard_rules
        )

        for rule in matched_vcard_rules:
            member_uids_by_rule.setdefault(rule, []).append(contact_uid)

        contact_vCards.append((contact_uid, contact_vCard_text))

    rule: VCardRuleBase
    for rule, rule_member_uids in member_uids_by_rule.items():
        if rule.GROUP_UID is None or rule.GROUP_TITLE is None:
            continue

        group_vCard_text = vcard_utils.VCardUtils.build_group(
            uid=rule.GROUP_UID,
            title=rule.GROUP_TITLE,
            member_uids=[
                member_uid
                for member_uid in rule_member_uids
            ]
        )

        group_vCards.append((rule.GROUP_UID, group_vCard_text))

    return contact_vCards, group_vCards


def _write_vCards_to_baikal_book(api: BaikalApi, user: str, vCards: list):
    if not vCards:
        return

    BAIKAL_BOOK = 'default'

    vCards_len = len(vCards)

    print_l(f'Передача карточек, количество: {vCards_len}')

    # Выгрузка контактов в Байкал
    for n, (uid, vCard_text) in enumerate(vCards, 1):
        print_l(f'Передача карточки {n} из {vCards_len}...')

        try:
            api.put_vCard(
                user=user,
                book=BAIKAL_BOOK,
                uid=uid,
                vCard_text=vCard_text
            )
        except requests.HTTPError as e:
            print_l(f"Ошибка передачи карточки в Байкал {e.response.status_code}, {e.response.text}")

    print_l('Передача завершена.')


# Обработка ведомого лидера
# ---leader - строка ведомого лидера
# ---parent_leader - строка ведущего лидера
# ---parent_archive - таблица из архива ведущего лидера (если есть)
# ---inData - входная выборка данных
def subleader_processing(leader, parent_leader, gcli, parent_archive=None, inData=None):
    # Чтение подотчетных ИД в массив
    def readIDsInArray(id_input, id_users, id_sponsors):
        temp = []
        for i in range(len(id_sponsors)):
            if id_input == id_sponsors[i]:
                temp.append(id_users[i])
        return temp

    # Рекуррентная функция поиска спонсоров
    def nestedSponsor(rangeSearch):
        if rangeSearch == []:
            return 0
        for i in rangeSearch:
            lvlDown = readIDsInArray(i, rangeUsers, rangeSponsors)
            rangeChildren.extend(lvlDown)
            nestedSponsor(lvlDown)

    # Поиск спонсора в архивных данных
    def seekSponsor(idx):
        try:
            sponsor = parent_archive.loc[idx, 'ID Спонсора']
            if sponsor in rangeUsers:
                return sponsor
            else:
                return seekSponsor(inputData, inputArchive, sponsor)
        except KeyError:
            return -1

    global LEVEL
    global ERRCOUNT_GOOGLE
    global STUCK_AT_GOOGLE
    global STUCK_AT_GOOGLE_SUB
    global RETRIES_SUB

    try:
        # dfloc = parent_wks[LDNAME].get_as_df(empty_value=np.nan)
        # dfloc = dfloc[dfloc[_ID] == inID]
        dfloc = parent_leader.copy()
        # print(dfloc)

        parent_buser = dfloc[_BAIKAL_USER]
        parent_bpass = dfloc[_BAIKAL_PASS]
        parent_name = dfloc[_NAME]
        parent_id = dfloc[_ID]
        parent_prefix = dfloc[_BAIKAL_PREFIX]
        parent_baikal_active = leader[_BAIKAL_ACTIVE]

        current_buser = leader[_BAIKAL_USER]
        current_bpass = leader[_BAIKAL_PASS]
        current_name = leader[_NAME]
        current_id = leader[_ID]
        current_url = leader[_URL]
        current_prefix = leader[_BAIKAL_PREFIX]
        current_baikal_active = leader[_BAIKAL_ACTIVE]
        current_qty = leader[_QTY]
        current_file = leader[_FILE]
        current_access = leader[_ACCESS]
        try:
            current_mconf_f = leader[_MCONF]
            current_mconf_r = re.compile(r'=HYPERLINK\(\"(.*)\";.*\)').search(current_mconf_f) if not pd.isna(
                current_mconf_f) else None
            # LEGACY
            if current_mconf_r is None:
                if pd.isna(current_mconf_f):
                    current_mconf = np.nan
                else:
                    current_mconf = leader[_MCONF]
                    check_code = re.compile(r"/file/d/([a-zA-Z0-9-_]+)").search(current_mconf)
                    if check_code is None:
                        current_mconf = np.nan
            else:
                current_mconf = current_mconf_r.group(1)
        except:
            current_mconf = np.nan
        current_email = leader[_EMAIL]

        refresh_time = int(_dt['dt_refresh_time'])

        print_l(f'=== {current_id} - {current_name} - Уровень {LEVEL} (Ведомый от {parent_id}) ===')

        loc_now = datetime.datetime.now()

        try:
            loc_date = datetime.datetime.strptime(leader[_UPDATE], "%d.%m.%Y %H:%M")
        except:
            print_l('Невозможно прочесть дату обновления. Обновляем запись лидера...')
            print_l('Текущее время: ' + loc_now.strftime("%d.%m.%Y %H:%M"))
            loc_delta = datetime.timedelta(hours=42)
        else:
            loc_delta = loc_now - loc_date
            print_l('Текущее время: ' + loc_now.strftime("%d.%m.%Y %H:%M"))
            print_l('Время обновления: ' + loc_date.strftime(
                "%d.%m.%Y %H:%M") + f' ({round(loc_delta.days * 24 + loc_delta.seconds / 3600, 1)} ч. назад)')

        URL_CREATED = not pd.isna(current_url)
        if pd.isna(current_url) and current_file == 'Да':
            print_l('Лидерская таблица не найдена! Создаем новую...')
            template, _ = load_google_sheet(gcli, _gs['temp_key'])
            new_sg = gcli.create(
                title=current_name[:2].upper() + ' ' + f'команда doTERRA {loc_now.strftime("%d.%m.%Y")}',
                template=template)
            current_url = new_sg.url
            URL_CREATED = True

        if URL_CREATED:
            perms = []
            sub_leaders = gcli.open_by_url(current_url)
            if "команда dt" in sub_leaders.title:
                sub_leaders.title = sub_leaders.title.replace("команда dt",
                                                              f'команда doTERRA {loc_now.strftime("%d.%m.%Y")}')
            else:
                sub_leaders.title = sub_leaders.title[:-10] + loc_now.strftime("%d.%m.%Y")
            for x in sub_leaders.permissions:
                if 'emailAddress' in x:
                    perms.append(x['emailAddress'].lower())
            if not pd.isna(leader["Email"]):
                if leader['Доступ'] == "Да":
                    for email in leader["Email"].split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted not in perms:
                            print(f"Выдаем доступ к таблице {formatted}")
                            sub_leaders.share(email.strip().replace(",", ""), role='writer', sendNotificationEmail=True)
                        else:
                            print(f"У {email} уже есть доступ к таблице")
                else:
                    for email in leader["Email"].split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted in perms:
                            print(f"Забираем доступ к таблице у {formatted}")
                            sub_leaders.remove_permission(formatted)

        # if loc_delta < datetime.timedelta(hours=refresh_time):
        # print_l(f'Запись уже обновлялась в течение последних {refresh_time} часов. Пропускаем...')
        # return leader

        print_l('Извлекаем ID ведомого лидера...')
        if inData is not None:
            dfTeamI = inData.copy()
        else:
            dfTeamI = pd.DataFrame(columns=['ID Спонсора'])

        rangeUsers = list(dfTeamI.index.values)

        # Проверка спонсоров - есть ли кто-то из цепочки, кто ушел в архив?
        dfSpon = dfTeamI.copy()
        if parent_archive is not None:
            dfSpon.loc[:, 'ID Спонсора'] = dfSpon.loc[:, 'ID Спонсора'].apply(
                lambda x: x if x in rangeUsers else seekSponsor(x)
            )

        rangeUsers = list(dfSpon.index.values)
        rangeSponsors = list(dfSpon['ID Спонсора'])
        rangeLeaders = [current_id]

        print_l('\nПОЛЬЗОВАТЕЛИ: ' + str(rangeUsers))
        print_l('\nСПОНСОРЫ: ' + str(rangeSponsors))
        print_l('\nЛИДЕР: ' + str(rangeLeaders) + ' ' + str(leader[_NAME]))

        rangeChildren = []
        topLvl = readIDsInArray(rangeLeaders[0], rangeUsers, rangeSponsors)
        rangeChildren.extend(topLvl)
        nestedSponsor(topLvl)

        if len(rangeChildren) > 0:
            dfOut = dfTeamI.loc[rangeChildren]
        else:
            dfOut = pd.DataFrame()

        print_l(f'Получено ID: {len(rangeChildren)}')
        current_qty = len(rangeChildren)

        print_l('Проверяем наличие пароля doTERRA...')
        if not pd.isna(leader[_DT_PASS]):
            print_l('Пароль найден! Погружаемся на уровень ниже...')
            LEVEL += 1
            output = leader_processing(leader, gcli)

            print_l('Работа на нижнем уровне завершена. Выходим...')
            LEVEL -= 1
            return output
        else:
            print_l('Пароль не найден. Продолжаем обработку...')
            # dfData = dfOut.copy().fillna('')
            leader_only = dfTeamI.loc[current_id].to_frame(name=current_id).T if current_id in dfTeamI.index else None
            if leader_only is not None:
                leader_only.loc[:, "Уровни"] = leader_only.loc[:, "Уровни"].fillna('0')
                leader_only.index.name = 'ID'
                dfData = pd.concat([
                    leader_only,
                    dfOut.copy().fillna('')
                ])
            else:
                dfData = dfOut.copy().fillna('')
            level_min = dfData["Уровни"].astype(int).min()
            print('Мин. уровень вложенности =', level_min)
            dfData.loc[:, "Уровни"] = dfData.loc[:, "Уровни"].astype(int) - level_min

        if GSheetUtils.parse_bool(current_baikal_active):
            if GSheetUtils.parse_bool(parent_baikal_active):
                print_l('Меняем префиксы в контактах из книги ведущего лидера...')
                _, __ = write_to_baikal(parent_buser, parent_bpass, dfData.iloc[1:, :],
                                        bprefix=current_prefix,
                                        cname=parent_name,
                                        cid=parent_id)

            print_l('Записываем контакты в личную книгу текущего ведомого лидера...')
            luser, lpass = write_to_baikal(current_buser, current_bpass, dfData.iloc[1:, :],
                                           bprefix=current_prefix,
                                           cname=current_name,
                                           cid=current_id)
            current_buser = luser
            current_bpass = lpass

        # ===== ===== ===== ===== =====
        # Генерация файла конфигурации
        if int(_mconf["enabled"]) and not pd.isna(current_url):
            lsh, lshList = load_google_sheet(gcli, current_url.split('/')[5])
            if lsh is not None and not pd.isna(current_email):
                print_l(f'Опрос mobileconfig...')
                lbaiconf_file = get_mobileconfig(current_buser, current_bpass, current_name)
                meta = {
                    'name': str(current_id) + '.mobileconfig'}
                media = MediaIoBaseUpload(lbaiconf_file, mimetype='application/x-apple-aspen-config')

                if pd.isna(current_mconf):
                    print_l(f'mobileconfig не обнаружен, создается новый...')
                    lbaiconf_res = lsh.client.drive._execute_request(
                        lsh.client.drive.service.files().create(
                            body=meta,
                            media_body=media
                        )
                    )
                # lbaiconf_res['permissions'] = []
                else:
                    print_l(f'Обновление mobileconfig...')
                    mkey = re.compile(r"/file/d/([a-zA-Z0-9-_]+)").search(current_mconf)
                    if mkey is None:
                        lbaiconf_id = current_mconf
                    else:
                        lbaiconf_id = mkey.group(1)
                    lbaiconf_res = lsh.client.drive._execute_request(
                        lsh.client.drive.service.files().update(
                            fileId=lbaiconf_id,
                            body=meta,
                            media_body=media
                        )
                    )
                lbaiconf_id = lbaiconf_res['id']
                # leader[_MCONF] = 'https://drive.google.com/file/d/'+lbaiconf_id
                strConf = 'https://drive.google.com/file/d/' + lbaiconf_id
                leader[_MCONF] = f'=HYPERLINK(\"{strConf}\";\"iOS\")'
                print(lbaiconf_res)
                print_l(f'Проверка разрешений mobileconfig...')
                lbaiconf_perms = lsh.client.drive._execute_request(
                    lsh.client.drive.service.permissions().list(
                        fileId=lbaiconf_id, fields='*'))['permissions']
                # print(lbaiconf_perms)
                perms = []
                for x in lbaiconf_perms:
                    if 'emailAddress' in x:
                        perms.append(x['emailAddress'].lower())
                if current_access == "Да":
                    for email in current_email.split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted not in perms:
                            print(f"Выдаем доступ к mobileconfig {formatted}")
                            lsh.client.drive._execute_request(
                                lsh.client.drive.service.permissions().create(
                                    fileId=lbaiconf_id,
                                    body={
                                        'type': 'user',
                                        'role': 'writer',
                                        'emailAddress': formatted,
                                        'sendNotificationEmail': True
                                    }
                                )
                            )
                        else:
                            print(f"У {email} уже есть доступ к mobileconfig...")

                else:
                    for email in current_email.split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted in perms:
                            print(f"Забираем доступ к mobileconfig у {formatted}...")
                            for x in lbaiconf_perms:
                                if email in x['emailAddress']:
                                    lsh.client.drive.delete_permissions(lbaiconf_id, x['id'])

        # ===== ===== ===== ===== =====

        # Запись полученных данных в лидерскую таблицу
        if not pd.isna(current_url) and current_url != "":
            print_l('Загружаем данные в ведомую лидерскую таблицу...')
            lsh, lshList = load_google_sheet(gcli, current_url.split('/')[5])
            df_coll = {item.title: item.get_as_df(empty_value=np.nan) for item in lsh.worksheets() if
                       item.title in WKSHEETS}
            df_coll[WKSHEETS[0]] = dfData
            upload_to_gsheets(lsh, df_coll)
            print_l('Проверяем таблицу на вложенность...')
            if LDNAME in lshList:
                dfLocLead = lshList[LDNAME].get_as_df(empty_value=np.nan)
                columns = list(dfLocLead.columns)
                i1 = 0
                for i in LD_COLUMNS:
                    if i[0] not in columns:
                        lshList[LDNAME].insert_cols(i1, number=1, values=None, inherit=False)  # добавляем столбец
                        lshList[LDNAME].update_value(f'{i[1]}1', i[0])
                    i1 += 1
                if dfLocLead.empty:
                    print_l('Обнаружена пустая таблица лидеров, погружаться некуда. Выходим...')
                else:
                    print_l('Зафиксирована вложенность! Погружаемся...')
                    LEVEL += 1
                    while not STUCK_AT_GOOGLE_SUB:
                        # dfLocLead = lshList[LDNAME].get_as_df(empty_value=np.nan)
                        dfLLMC = lshList[LDNAME].get_as_df(empty_value=np.nan, start='P1', value_render='FORMULA')
                        dfLocLead.update(dfLLMC)
                        print_l(f'Попытка сбора № {RETRIES_SUB}')
                        srLocLead = leader.copy().fillna('')
                        srLocLead[_URL] = current_url
                        srLocLead[_QTY] = current_qty
                        srLocLead[_UPDATE] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                        srLocLead[_BAIKAL_USER] = current_buser
                        srLocLead[_BAIKAL_PASS] = current_bpass
                        dfEmbed = dfLocLead.apply(lambda x: subleader_processing(x, srLocLead,
                                                                                 gcli, parent_archive,
                                                                                 inData=dfData), axis=1)
                        upload_leaders_to_gsheets(lsh, dfEmbed)
                        if not STUCK_AT_GOOGLE_SUB:
                            RETRIES_SUB = 0
                            break
                        else:
                            print_l(f'Произошел сбой при попытке обработать ведомого лидера. Пробуем еще раз...')
                            RETRIES_SUB += 1
                            if RETRIES_SUB > 2:
                                RETRIES_SUB = 0
                                raise ValueError('Закончились попытки обработки ведомого лидера')
                            STUCK_AT_GOOGLE_SUB = 0
                    print_l('Работа на нижнем уровне завершена. Выходим...')
                    LEVEL -= 1
            else:
                print_l('Вложенность отсутствует. Выходим...')
        if not pd.isna(current_url) and current_url != "":
            lists_ = leader['Листы']
            to_delete = []
            sub_leaders = gcli.open_by_url(current_url)
            if "команда dt" in sub_leaders.title:
                sub_leaders.title = sub_leaders.title.replace("команда dt",
                                                              f'команда doTERRA {loc_now.strftime("%d.%m.%Y")}')
            else:
                sub_leaders.title = sub_leaders.title[:-10] + loc_now.strftime("%d.%m.%Y")
            sub_worksheets = [x for x in sub_leaders.worksheets()]
            wk_titles = [x.title for x in sub_worksheets]
            if lists_ == "Только бонусы":
                for x in sub_worksheets:
                    r = check_leaders(x)
                    if (r is None and "Бонус" not in x.title) or r:
                        to_delete.append(x)
            elif lists_ == "Без изменений":
                for x in sub_worksheets:
                    if 'Test' in x.title:
                        sub_leaders.del_worksheet(x)
                        continue
            elif lists_ == "Все":
                """for x in bonus_worksheets:
                    r = check_leaders(x)
                    if (r is None and "Test" in x.title) or r:
                        to_delete.append(x)"""
                pass
            elif pd.isna(lists_):
                if 'Test' not in wk_titles:
                    sub_leaders.add_worksheet('Test')
                for x in sub_worksheets:
                    r = check_leaders(x)
                    if (r is None and "Test" not in x.title) or r:
                        to_delete.append(x)
            for x in to_delete:
                sub_leaders.del_worksheet(x)
        # Обновление строки лидера в исходной таблице
        output = leader.copy().fillna('')
        output[_URL] = current_url
        output[_QTY] = current_qty
        output[_UPDATE] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        output[_BAIKAL_USER] = current_buser
        output[_BAIKAL_PASS] = current_bpass

        FLAG_SUCCESS_SUB = 1
        return output

    except:
        print(f'===== [#ERROR] Невозможно обработать данные по ведомому лидеру {leader[_ID]}. Пробуем еще раз... =====')
        traceback.print_exc()

        ERRCOUNT_GOOGLE += 1
        STUCK_AT_GOOGLE = 1
        ERRSTACK.append(
            [f'Google - Обработка ведомых лидеров (Уровень {LEVEL})',
             f'Невозможно обработать данные по ведомому лидеру {leader[_ID]} ({leader[_NAME]}).',
             traceback.format_exc()
             ]
        )
        # raise ValueError('Ошибка при обработке ведомых лидеров')
        return leader


def check_leaders(leaders: pygsheets.Worksheet):
    if leaders.title != "Лидеры":
        return None
    df = leaders.get_as_df(empty_value=np.nan)
    if df.empty:
        return True
    leaders.hidden = True
    return False


# Обработка лидера
def leader_processing(leader, gcli):
    global LEVEL
    global ERRCOUNT_GOOGLE
    global STUCK_AT_GOOGLE
    global STUCK_AT_GOOGLE_SUB
    global RETRIES_SUB
    try:
        print_l('===== ===== ===== ===== =====')

        lname = leader[_NAME]
        lid = leader[_ID]
        ldtpass = leader[_DT_PASS]
        ldsbid = leader[_SBID]
        lurl = leader[_URL]
        lbaikal = leader[_BAIKAL_ACTIVE]

        lqty = leader[_QTY]
        lfile = leader[_FILE]
        lemail = leader[_EMAIL]
        laccess = leader[_ACCESS]

        print_l(f'=== {lid} - {lname} - Уровень {LEVEL} ===')

        lnow = datetime.datetime.now()

        refresh_time = int(_dt['dt_refresh_time'])

        try:
            ldate = datetime.datetime.strptime(leader[_UPDATE], "%d.%m.%Y %H:%M")
        except:
            print_l('Невозможно прочесть дату обновления. Обновляем запись лидера...')
            print_l('Текущее время: ' + lnow.strftime("%d.%m.%Y %H:%M"))
            ldelta = datetime.timedelta(hours=42)
        else:
            ldelta = lnow - ldate
            print_l('Текущее время: ' + lnow.strftime("%d.%m.%Y %H:%M"))
            print_l('Время обновления: ' + ldate.strftime(
                "%d.%m.%Y %H:%M") + f' ({round(ldelta.days * 24 + ldelta.seconds / 3600, 1)} ч. назад)')

        if pd.isna(lurl) and lfile == 'Да':
            print_l('Ссылка на таблицу отсутствует! Генерируем новую...')
            template, _ = load_google_sheet(gcli, _gs['temp_key'])
            # new_sg = gcli.create(title=lname[:2].upper() + ' ' + f'команда doTERRA {lnow.strftime("%d.%m.%Y")}', template=template)
            new_sg = gcli.create(title=lname.upper() + ' ' + f'команда doTERRA {lnow.strftime("%d.%m.%Y")}',
                                 template=template)
            lurl = new_sg.url

        if not pd.isna(lemail):
            sub_leaders = gcli.open_by_url(lurl)
            if "команда dt" in sub_leaders.title:
                sub_leaders.title = sub_leaders.title.replace("команда dt",
                                                              f'команда doTERRA {lnow.strftime("%d.%m.%Y")}')
            else:
                sub_leaders.title = sub_leaders.title[:-10] + lnow.strftime("%d.%m.%Y")
            perms = []
            for x in sub_leaders.permissions:
                if 'emailAddress' in x:
                    perms.append(x['emailAddress'].lower())
            if not pd.isna(lemail):
                if leader['Доступ'] == "Да":
                    for email in lemail.split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted not in perms:
                            print(f"Выдаем доступ к таблице {formatted}")
                            sub_leaders.share(email.strip().replace(",", ""), role='writer', sendNotificationEmail=True)
                        else:
                            print(f"У {email} уже есть доступ к таблице")
                else:
                    for email in leader["Email"].split(","):
                        formatted = email.strip().replace(",", "").lower()
                        if formatted in perms:
                            print(f"Забираем доступ к таблице у {formatted}")
                            sub_leaders.remove_permission(formatted)

        # if ldelta < datetime.timedelta(hours=refresh_time):
        # print_l(f'Запись уже обновлялась в течение последних {refresh_time} часов. Пропускаем...')
        # return leader

        # lqty = leader['К-во']

        leader_baikal_prefix = leader[_BAIKAL_PREFIX]
        leader_baikal_active = leader[_BAIKAL_ACTIVE]
        leader_baikal_user = leader[_BAIKAL_USER]
        leader_baikal_pass = leader[_BAIKAL_PASS]
        leader_baikal_conf_f = leader[_MCONF]
        leader_baikal_conf_r = re.compile(r'=HYPERLINK\(\"(.*)\";.*\)').search(leader_baikal_conf_f) if not pd.isna(
            leader_baikal_conf_f) else None
        # LEGACY
        if leader_baikal_conf_r is None:
            if pd.isna(leader_baikal_conf_f):
                leader_baikal_conf = np.nan
            else:
                leader_baikal_conf = leader[_MCONF]
                check_code = re.compile(r"/file/d/([a-zA-Z0-9-_]+)").search(leader_baikal_conf)
                if check_code is None:
                    leader_baikal_conf = np.nan
        else:
            leader_baikal_conf = leader_baikal_conf_r.group(1)

        df_coll = pd.DataFrame()

        print_l(lname + ' ' + str(lid))
        # ПАРСИНГ ИЗ ЛИЧНОГО КАБИНЕТА
        if not pd.isna(ldtpass) or DEMO_MODE:
            if not DEMO_MODE:
                soup, language = get_doterra_db(lid, ldtpass)
                lsh, lshList, df_coll, lqty = parse_doterra_db(soup, gcli, lurl, language,
                                                               True if lfile == 'Да' else False)

            else:
                lsh, lshList, df_coll, lqty = parse_demo(gcli, lurl, True if lfile == 'Да' else False)

            if not DEMO_MODE:
                # Отправка сообщения в Salebot
                if ldsbid != '':
                    # send_salebot_variables(ldsbid, df_coll[WKSHEETS[0]])

                    send_SaleBot(_salebot['salebot_url'], ldsbid, lqty)
                if not pd.isna(lurl) and lfile == 'Да':
                    upload_to_gsheets(lsh, df_coll)

            # save data for mocking
            # import pickle
            # with open(f"{lid}.pkl", "wb") as f:
            # 	pickle.dump((lsh, lshList, df_coll, lqty), f)

            if GSheetUtils.parse_bool(leader_baikal_active):
                # Актуализация аккаунта Baikal
                leader_baikal_user, leader_baikal_pass = write_to_baikal(leader_baikal_user, leader_baikal_pass,
                                                                         df_coll[WKSHEETS[0]],
                                                                         bprefix=leader_baikal_prefix,
                                                                         cname=lname,
                                                                         cid=lid)
                # ===== ===== ===== ===== =====
                # Генерация файла конфигурации
                '''
                if not pd.isna(lurl):
                    if lsh is not None and not pd.isna(lemail):
                        print_l(f'Опрос mobileconfig...')
                        lbaiconf_file = get_mobileconfig(lbaiuser, lbaipass, lname)
                        meta = {
                            'name': str(lid)+'.mobileconfig'}
                        media = MediaIoBaseUpload(lbaiconf_file, mimetype='application/x-apple-aspen-config')

                        if pd.isna(lbaiconf):
                            print_l(f'mobileconfig не обнаружен, создается новый...')
                            lbaiconf_res = lsh.client.drive._execute_request(
                                lsh.client.drive.service.files().create(
                                    body=meta,
                                    media_body=media					
                                )
                            )
                            # lbaiconf_res['permissions'] = []
                        else:
                            print_l(f'Обновление mobileconfig...')
                            mkey = re.compile(r"/file/d/([a-zA-Z0-9-_]+)").search(lbaiconf)
                            if mkey is None:
                                lbaiconf_id = lbaiconf
                            else:
                                lbaiconf_id = mkey.group(1)
                            lbaiconf_res = lsh.client.drive._execute_request(
                                lsh.client.drive.service.files().update(
                                    fileId=lbaiconf_id,
                                    body=meta,
                                    media_body=media					
                                )
                            )
                        lbaiconf_id = lbaiconf_res['id']
                        #leader[_MCONF] = 'https://drive.google.com/file/d/'+lbaiconf_id 
                        strConf = 'https://drive.google.com/file/d/'+lbaiconf_id
                        leader[_MCONF] = f'=HYPERLINK(\"{strConf}\";\"iOS\")'
                        print(lbaiconf_res)
                        print_l(f'Проверка разрешений mobileconfig...')
                        lbaiconf_perms = lsh.client.drive._execute_request(
                            lsh.client.drive.service.permissions().list(
                                fileId=lbaiconf_id, fields='*'))['permissions']
                        # print(lbaiconf_perms)
                        perms = []
                        for x in lbaiconf_perms:
                            if 'emailAddress' in x:
                                perms.append(x['emailAddress'].lower())
                        if laccess == "Да":
                            for email in lemail.split(","):
                                formatted = email.strip().replace(",", "").lower()
                                if formatted not in perms:
                                    print(f"Выдаем доступ к mobileconfig {formatted}")
                                    lsh.client.drive._execute_request(
                                        lsh.client.drive.service.permissions().create(
                                            fileId=lbaiconf_id,
                                            body={
                                                'type':'user',
                                                'role':'writer',
                                                'emailAddress': formatted,
                                                'sendNotificationEmail': True                                            
                                            }			
                                        )
                                    )
                                else:
                                    print(f"У {email} уже есть доступ к mobileconfig...")

                        else:
                            for email in lemail.split(","):
                                formatted = email.strip().replace(",", "").lower()
                                if formatted in perms:
                                    print(f"Забираем доступ к mobileconfig у {formatted}...")
                                    for x in lbaiconf_perms:
                                        if email in x['emailAddress']:
                                            lsh.client.drive.delete_permissions(lbaiconf_id, x['id'])
                # ===== ===== ===== ===== =====
                '''
            # Обработка ведомых лидеров
            if not pd.isna(lshList) and LDNAME in lshList:
                while not STUCK_AT_GOOGLE_SUB:
                    # Проверка на наличие колонок
                    ldf = lshList[LDNAME].get_as_df(empty_value=np.nan)
                    columns = list(ldf.columns)
                    i1 = 0
                    for i in LD_COLUMNS:
                        if i[0] not in columns:
                            lshList[LDNAME].insert_cols(i1, number=1, values=None, inherit=False)  # добавляем столбец
                            lshList[LDNAME].update_value(f'{i[1]}1', i[0])
                        i1 += 1
                    try:
                        archdf = lshList[ARCHNAME].get_as_df(empty_value=np.nan)
                        archdf = archdf.set_index('ID')
                    except:
                        archdf = None
                    lsr = leader.copy().fillna('')
                    lsr[_URL] = lurl
                    lsr[_QTY] = lqty
                    lsr[_UPDATE] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                    lsr[_BAIKAL_USER] = leader_baikal_user
                    lsr[_BAIKAL_PASS] = leader_baikal_pass
                    print_l('Начинаем обработку ведомых лидеров...')
                    LEVEL += 1
                    # Только столбец mobileconfig
                    ldfmc = lshList[LDNAME].get_as_df(empty_value=np.nan, start='P1', value_render='FORMULA')
                    ldf.update(ldfmc)
                    if not ldf.empty:
                        ldfLevel = ldf.apply(lambda x: subleader_processing(x, lsr,
                                                                            gcli, parent_archive=archdf,
                                                                            inData=df_coll[WKSHEETS[0]]), axis=1)
                        upload_leaders_to_gsheets(lsh, ldfLevel)
                        if not STUCK_AT_GOOGLE_SUB:
                            RETRIES_SUB = 0
                            break
                        else:
                            print_l(f'Произошел сбой при попытке обработать ведомого лидера. Пробуем еще раз...')
                            RETRIES_SUB += 1
                            if RETRIES_SUB > 2:
                                RETRIES_SUB = 0
                                raise ValueError('Закончились попытки обработки ведомого лидера')
                            STUCK_AT_GOOGLE_SUB = 0
                    else:
                        print_l('Таблица Лидеры пустая. Пропускаем...')
                        RETRIES_SUB = 0
                        break
                LEVEL -= 1
                print_l('Обработка ведомых лидеров завершена.')
            else:
                print_l('Таблица Лидеры отсутствует. Пропускаем...')
        else:
            print_l('Нет пароля от doTERRA. Пропускаем...')
        # print(lid, ltable)
        lists_ = leader['Листы']
        to_delete = []
        sub_leaders = gcli.open_by_url(lurl)
        if "команда dt" in sub_leaders.title:
            sub_leaders.title = sub_leaders.title.replace("команда dt", f'команда doTERRA {lnow.strftime("%d.%m.%Y")}')
        else:
            sub_leaders.title = sub_leaders.title[:-10] + lnow.strftime("%d.%m.%Y")
        sub_worksheets = [x for x in sub_leaders.worksheets()]
        wk_titles = [x.title for x in sub_worksheets]
        if lists_ == "Только бонусы":
            for x in sub_worksheets:
                r = check_leaders(x)
                if (r is None and "Бонус" not in x.title) or r:
                    to_delete.append(x)
        elif lists_ == "Без изменений":
            for x in sub_worksheets:
                if 'Test' in x.title:
                    sub_leaders.del_worksheet(x)
                    continue
        elif lists_ == "Все":
            """for x in bonus_worksheets:
                r = check_leaders(x)
                if (r is None and "Test" in x.title) or r:
                    to_delete.append(x)"""
            pass
        elif pd.isna(lists_):
            if 'Test' not in wk_titles:
                sub_leaders.add_worksheet('Test')
            for x in sub_worksheets:
                r = check_leaders(x)
                if (r is None and "Test" not in x.title) or r:
                    to_delete.append(x)
        for x in to_delete:
            sub_leaders.del_worksheet(x)
        # Обновление строки лидера в исходной таблице
        output = leader.copy().fillna('')
        output[_URL] = lurl
        output[_QTY] = lqty
        output[_UPDATE] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        output[_BAIKAL_USER] = leader_baikal_user
        output[_BAIKAL_PASS] = leader_baikal_pass
        return output
    except:
        # print(f'===== [#ERROR] Невозможно обработать данные по лидеру {leader}. Пропускаем... =====')
        traceback.print_exc()

        ERRCOUNT_GOOGLE += 1
        STUCK_AT_GOOGLE = 1
        ERRSTACK.append(
            [f'Google - Обработка лидеров (Уровень {LEVEL})',
             # f'Невозможно обработать данные по лидеру {leader}.',
             traceback.format_exc()]
        )
        return leader


# Главная функция обработки корневой таблицы
def core_processing(sh: pygsheets.Spreadsheet, wk, gcli, emIn):
    global STUCK_AT_GOOGLE
    global RETRIES
    try:
        if LDNAME in wk:
            while not STUCK_AT_GOOGLE:
                # Проверка на наличие колонок
                df: pd.DataFrame = wk[LDNAME].get_as_df(empty_value=np.nan)
                columns = list(df.columns)
                i1 = 0
                for i in LD_COLUMNS:
                    if i[0] not in columns:
                        wk[LDNAME].insert_cols(i1, number=1, values=None, inherit=False)  # добавляем столбец
                        wk[LDNAME].update_value(f'{i[1]}1', i[0])
                    i1 += 1
                ss = gcli.open_by_url(sh.url)
                if "команда dt" in ss.title:
                    ss.title = ss.title.replace("команда dt",
                                                f'команда doTERRA {datetime.datetime.now().strftime("%d.%m.%Y")}')
                else:
                    ss.title = ss.title[:-10] + datetime.datetime.now().strftime("%d.%m.%Y")
                # Вся таблица целиком
                df = ss.worksheet_by_title(LDNAME).get_as_df(empty_value=np.nan)

                # Только столбец mobileconfig (в режиме FORMULA)
                dfmc = ss.worksheet_by_title(LDNAME).get_as_df(empty_value=np.nan, start='P1', value_render='FORMULA')
                df.update(dfmc)
                dfCore = df.apply(lambda x: leader_processing(x, gcli), axis=1)
                upload_leaders_to_gsheets(sh, dfCore)
                if not STUCK_AT_GOOGLE:
                    RETRIES = 0
                    break
                else:
                    print_l(f'Произошел сбой при попытке обработать одного из лидеров. Пробуем еще раз...')
                    RETRIES += 1
                    if RETRIES > 2:
                        RETRIES = 0
                        raise ValueError('Закончились попытки обработки в основной таблице!')
                    STUCK_AT_GOOGLE = 0
            sendMail(emIn, errstack=ERRSTACK, success=True)
            print_l('Парсинг успешно завершен! Запускаем генерацию бонуса...')
    except:
        ERRSTACK.append(
            [f'Google - Глобальный парсинг',
             f'Невозможно завершить процесс парсинга таблиц.',
             traceback.format_exc()
             ]
        )
        sendMail(emIn, errstack=ERRSTACK, success=False)
        print_l('Парсинг завершен с ошибками. Запускаем генерацию бонуса...')
    finally:
        cmdBonus = [
            "/usr/local/bin/python3.8",
            os.path.join(os.path.dirname(__file__), 'dt_crm_bonus.py'),
            os.path.join(os.path.dirname(__file__), 'dt_combo.ini')
        ]
        if DEMO_MODE:
            cmdBonus.append("--demo")
        subprocess.Popen(cmdBonus)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====


def main():
    global _dt, _gs, _msql, _bkl, _vc, _email, _salebot, _mconf

    me = singleton.SingleInstance()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("config", help='path to .ini config file (doTERRA credentials + Google Spreadsheet key)')
    arg_parser.add_argument("--demo", help='run script in demo mode (optional)', nargs='?',
                            const=True, default=False)
    args = arg_parser.parse_args()

    config = args.config

    DEMO_MODE = args.demo

    # sys.stdout.reconfigure(encoding='cp1251')
    locale.setlocale(locale.LC_TIME, 'ru_RU')
    locale.setlocale(locale.LC_NUMERIC, 'ru_RU')
    LOGGER.setLevel(logging.WARNING)

    print('Подключаемся к Google Api...')
    print('HHHHHHHHHH')
    print_l('HHHHHHHHHH')
    google_sheets_api = pygsheets.authorize(client_secret='pythontest/clsedtr.json')
    print('Авторизация завершена.')

    # Загрузка конфигурации
    sourceRes = configparser.ConfigParser()
    sourceRes.read(config, encoding='utf-8')

    _dt = sourceRes['doTERRA']
    _gs = sourceRes['Google']
    _msql = sourceRes['MySQL']
    _bkl = sourceRes['Baikal']
    _vc = sourceRes['vCard']
    _email = sourceRes['E-mail']
    _salebot = sourceRes['SaleBot']
    _mconf = sourceRes['MobileConfig']

    if not DEMO_MODE:
        core_sh, core_wk = load_google_sheet(google_sheets_api, _gs['core_key'], core=True)
        core_processing(core_sh, core_wk, google_sheets_api, _email)
    else:
        print("==================================")
        print("===== ДЕМОНСТРАЦИОННЫЙ РЕЖИМ =====")
        print("==================================")
        demo_sh, demo_wk = load_google_sheet(google_sheets_api, _gs['demo_key'], core=True)
        core_processing(demo_sh, demo_wk, google_sheets_api, _email)


if __name__ == '__main__':
    main()
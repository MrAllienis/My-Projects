# Библиотеки
import datetime
import calendar
import locale
import traceback

import smtplib
from email.message import EmailMessage

import pandas as pd
import numpy as np

import pygsheets

import argparse
import configparser

from tendo import singleton

import dt_crm_app
from salebot_api import SalebotApi

# Глобальные переменные
# Листы в таблицах
SHEETS = ['Команда', 'Бонусы', 'Лидеры']

# Флаг успешности операции
MSG_SUCCESS = True
# Этап, на котором застопорилось выполнение скрипта
MSG_STAGE = ''
# Текст ошибки
MSG_ERROR = ''
# Трассировка Python
MSG_TRACE = ''

# Имена столбцов таблицы Лидеры
_URL = 'URL'

# Имена столбцов таблицы Команда (для расчета бонуса)
_ID = 'ID'
_NAME = 'Имя'
_FNAME = 'Фамилия'
_LEVELS = 'Уровни'
_SPONSOR_ID = 'ID Спонсора'
_SIGNUP_DATE = 'Дата подписания'
_RECRUITER_NAME = 'Имя Рекрутера'
_RECRUITER_ID = 'ID Рекрутера'
_SPONSOR_NAME = 'Имя Спонсора'
_LAST_ORDER_DATE = 'Дата последнего заказа'
_PHONE = 'Телефон'
_CELL_PHONE = 'Cell'
_WORK_PHONE = 'Work'

# Имена столбцов бонусной выкладки
_BONUS_LEVEL = 'Уровень'
_BONUS_LEADER = "Лидер"
_BONUS_LRP = "LRP"
_BONUS_PV = "PV"
_BONUS_OV = "OV"
_BONUS_USD = "USD"

# Папка в которой хранятся опубликованные таблицы с бонусами
BONUS_PUBLIC_FOLDER_NAME = "public"

# Уровень погруженности
LEVEL = 0

# Буфер
BUF = []
ERRSTACK = []

EMAIL_SENT = False

DEMO_MODE = False


# Печать с записью в буфер и сдвигом в зависимости от уровня
def print_l(_str):
    res = LEVEL * '- ' + str(_str)
    print(res)
    BUF.append(res)
    if len(BUF) > 10:
        BUF.pop(0)


# Отправка почты
# ([sta, err, tra], [sta, err, tra], [sta, err, tra], ...) = errstack
def send_mail(errstack=None, success=True):
    global EMAIL_SENT
    if not EMAIL_SENT:
        # Настройка почтового сервера
        mail_set = _email

        _smtp_server = mail_set['server']
        _smtp_port = mail_set['port']
        fromaddr = mail_set['addr_source']
        frompass = mail_set['pass']
        toaddr = mail_set['addr_dest']

        # Формирование сообщения
        strDate = datetime.datetime.now().ctime()
        status = 'НЕИЗВЕСТНО'
        strMess = f'Это тестовое сообщение. Если вы видите его на экране, то проверка статуса по какой-либо причине ' \
                  f'не сработала.\n\nВыход консоли (для разработчика): {traceback.format_exc()} '
        if not success:
            strErrStack = [
                "ЭТАП: {}\nОШИБКА: {}\nТРАССИРОВКА: {}\n===== ===== ===== ===== =====\n".format(x[0], x[1], x[2]) for x
                in errstack]
            status = 'КРИТИЧЕСКАЯ ОШИБКА'
            strMess = "Во время выполнения скрипта произошла критическая ошибка. Программа была аварийно завершена.\n\n" \
                      + "Обратитесь к разработчику за консультацией.\n\n" \
                      + "Последний вывод консоли:\n{}\n\n".format('\n'.join(BUF)) \
                      + "Трассировка консоли:\n{}\n\n".format(traceback.format_exc()) \
                      + "Также были выявлены следующие ошибки:\n" + "\n".join(strErrStack)
        elif errstack:
            strErrStack = [
                "ЭТАП: {}\nОШИБКА: {}\nТРАССИРОВКА: {}\n===== ===== ===== ===== =====\n".format(x[0], x[1], x[2]) for x
                in errstack]
            status = 'УСПЕХ, ЕСТЬ ОШИБКИ'
            strMess = "Выполнение скрипта завершено успешно. Во время выполнения возникли следующие ошибки:\n\n" + "\n".join(
                strErrStack)
        else:
            status = 'УСПЕХ'
            strMess = "Выполнение скрипта завершено успешно. Ошибок нет.\n\n"

        msg = EmailMessage()
        msg.set_content(strDate + '\n' + strMess)
        msg['Subject'] = f'[{status}] - Bonus ({strDate})'
        msg['From'] = fromaddr
        msg['To'] = toaddr

        s = smtplib.SMTP_SSL(_smtp_server, _smtp_port)
        s.login(fromaddr, frompass)
        s.send_message(msg)
        s.quit()
        #		EMAIL_SENT = True
        EMAIL_SENT = False


# Загрузка таблицы Google
def load_google_sheet(gs_key, core=False, bonus_only=False):
    try:
        def sheet_status(label):
            print_l(label.upper() + ' - ' + ('ЕСТЬ' if label in res else 'ОТСУТСТВУЕТ'))
            if label not in res:
                print_l('Восстанавливаем таблицу ' + label + '...')
                crm_spreadsheet.add_worksheet(title=label)

        print_l('Открываем таблицы CRM...')
        crm_spreadsheet = google_sheets_api.open_by_key(gs_key)
        res = {crm_spreadsheet.sheet1.title: crm_spreadsheet.sheet1}

        if not core:
            print_l('ИМЯ ТАБЛИЦЫ: ' + crm_spreadsheet.title)
            # {'название_таблицы': сама таблица}
            res = {item.title: item for item in crm_spreadsheet.worksheets()}
            print_l('Проверяем наличие страниц...')
            for sheet_name in SHEETS:
                sheet_status(sheet_name)

            # Дублируем для принятия изменений
            crm_spreadsheet = google_sheets_api.open_by_key(gs_key)
            res = {item.title: item for item in crm_spreadsheet.worksheets()}
        else:
            print_l('Открыта корневая таблица.')

        return crm_spreadsheet, res

    except:
        ERRSTACK.append(
            [
                f'Google - Открытие таблицы (Уровень {LEVEL})',
                f'Невозможно открыть Google Таблицу (ключ = {gs_key})',
                traceback.format_exc()
            ]
        )
        print(f'Google - Открытие таблицы (Уровень {LEVEL})', '\n',
              f'Невозможно открыть Google Таблицу (ключ = {gs_key})')
        print('===== [#ERROR] Ошибка при подключении к таблице Google =====')
        raise ValueError


def bonus_processing(leader_row: pd.Series, team_sheet: pygsheets.Worksheet, current_date=datetime.datetime.now()):
    # Форматы ячеек
    EMPTY = pygsheets.Cell("A1")

    GOOD = pygsheets.Cell("A1")
    BAD = pygsheets.Cell("A1")
    WORST = pygsheets.Cell("A1")

    LEVEL1 = pygsheets.Cell("A1")
    LEVEL2 = pygsheets.Cell("A1")
    LEVEL3 = pygsheets.Cell("A1")

    EMPTY.color = tuple(map(float, _bonus['color_empty'].split(',')))
    EMPTY.set_text_format('bold', False)

    GOOD.color = tuple(map(float, _bonus['color_good'].split(',')))
    BAD.color = tuple(map(float, _bonus['color_bad'].split(',')))
    WORST.color = tuple(map(float, _bonus['color_worst'].split(',')))

    LEVEL1.color = tuple(map(float, _bonus['color_lvl1'].split(',')))
    LEVEL2.color = tuple(map(float, _bonus['color_lvl2'].split(',')))
    LEVEL3.color = tuple(map(float, _bonus['color_lvl3'].split(',')))

    def dateExtract(x: pd.DataFrame):
        def dropPV(xx):
            for ae in ['OV', 'PV', 'LRP PV']:
                if ae in xx:
                    return xx.replace(ae + ' ', '')
            return xx

        # Сортировка дат из таблицы команда
        colSource = x.columns
        colDates = colSource.map(
            lambda x: pd.to_datetime(
                dropPV(x), errors='coerce', format='%m.%y'
            )).dropna().unique().sort_values(ascending=False)

        localOrder = []
        for i in colDates:
            for o in ['OV', 'PV', 'LRP PV']:
                localOrder.append(i.strftime(o + ' %m.%y'))

        # Выделение данных для обработки
        # Сначала ИД, имена-фамилии и уровни вложенности
        c = x.drop(localOrder, axis=1)[
            [_ID, _FNAME, _NAME, _LEVELS, _SPONSOR_ID, _SIGNUP_DATE, _RECRUITER_NAME, _RECRUITER_ID, _SPONSOR_NAME,
             _LAST_ORDER_DATE, _PHONE, _CELL_PHONE, _WORK_PHONE]]
        c[_LEVELS] = c[_LEVELS].fillna(0).astype(int)
        # Проверяем флаг на перекрытие сдвига по месяцу
        offovrd = _bonus['month_override']
        # Если есть перекрытие, считаем сдвиг по month_offset, иначе считаем
        # со сдвигом 1 для дней с 1 по 12 и сдвигом 0 для остальных дней
        if offovrd == '1':
            offs = _bonus['month_offset']
        else:
            day_today = current_date.day
            if day_today in [i + 1 for i in range(12)]:
                offs = '1'
            else:
                offs = '0'
        if DEMO_MODE:
            offs = _bonus['demo_offset']
        # 0: d = x[localOrder].iloc[:,0:3]
        # 1: d = x[localOrder].iloc[:,3:6]
        d = x[localOrder].iloc[:, int(offs) * 3:int(offs) * 3 + 3]
        # c['PV от следующего заказа LRP'] = c['PV от следующего заказа LRP'].apply(lambda mc: locale.atof(str(mc)))
        # d = x[localOrder].applymap(lambda mc: locale.atof(str(mc).replace('^','')))
        res = pd.concat([c, d], axis=1).fillna(0)
        return res

    def get_subleaders(x, src):
        _parent = x[_ID]
        y = src[src[_SPONSOR_ID] == _parent] if (x[_LEVELS] <= 2) else pd.DataFrame()
        if not y.empty:
            y.loc[:, ['SUB']] = y.apply(lambda y: get_subleaders(y, src), axis=1)
        return y

    def get_scoreboard(x):
        '''
        На вывод:
        _BONUS_LEVEL='Уровень'
        _BONUS_LEADER="Лидер"
        _BONUS_LRP="LRP"
        _BONUS_PV="PV"
        _BONUS_OV="OV"
        _BONUS_USD="USD"

        Служебные
        _ID = "ID"
        _SPONSOR_ID = "ID Спонсора"
        '''

        # tblTest = pd.concat([leader0[[_LEVELS,_FNAME,_NAME]], leader0.iloc[:,-1]], axis=1)
        y = pd.Series(dtype='object')
        # print(x)
        y[_BONUS_LEVEL] = x[_LEVELS]
        # y[_BONUS_LEADER] = str(x[_FNAME]) + ' ' + str(x[_NAME])
        url = f'{_dt["dt_per_url"]}&DISTID2={x[_ID]}'
        y[_BONUS_LEADER] = '=ГИПЕРССЫЛКА("{}"; "{} {}")'.format(url, str(x[_FNAME]), str(x[_NAME]))
        y[_BONUS_LRP] = float(str(x.iloc[-2]).replace(',', '.'))
        y[_BONUS_PV] = float(str(x.iloc[-3]).replace(',', '.'))
        y[_BONUS_OV] = 0
        y[_BONUS_USD] = 0
        y[_ID] = x[_ID]
        y[_SPONSOR_ID] = x[_SPONSOR_ID]
        y[_SIGNUP_DATE] = x[_SIGNUP_DATE]
        y[_RECRUITER_NAME] = x[_RECRUITER_NAME]
        y[_RECRUITER_ID] = x[_RECRUITER_ID]
        y[_SPONSOR_NAME] = x[_SPONSOR_NAME]
        y[_LAST_ORDER_DATE] = x[_LAST_ORDER_DATE]
        y[_PHONE] = x[_PHONE]
        y[_CELL_PHONE] = x[_CELL_PHONE]
        y[_WORK_PHONE] = x[_WORK_PHONE]

        y['FLAG_PARENT_100'] = 0
        y['FLAG_3_CHILDREN_100'] = 0
        y['FLAG_ALTOGETHER_600'] = 0

        y['FLAG_BONUS_50'] = 0
        y['FLAG_BONUS_250'] = 0
        y['FLAG_BONUS_1500'] = 0

        y['FLAG_PENALTY'] = 0
        y['FLAG_NEWCOMER'] = 0

        return y

    def get_leader_with_subs(x):
        if x['SUB'].empty:
            return x.to_frame().T
        else:
            y = x['SUB'].apply(lambda z: pd.concat([z.to_frame().T, z['SUB']]), axis=1)
            y = pd.concat(y.values)
            return pd.concat([x.to_frame().T, y])

    # Проверка оснований выплаты бонусов
    def check_parent_100(x):
        vLRP = x[_BONUS_LRP]
        res = 1 if vLRP >= 100 else 0
        return res

    def check_3_children_100(x, src):
        if x[_BONUS_LEVEL] == 3:
            return 0

        children = src[src[_SPONSOR_ID] == x[_ID]]
        if children.empty:
            return 0

        vLRP = children.apply(check_parent_100, axis=1)

        res = vLRP.sum() // 3
        return res

    def calculate_ov(x, src):
        if x[_BONUS_LEVEL] == 3:
            return 0

        # Вывод ведомых
        children = src[src['ID Спонсора'] == x['ID']]

        # Учет LRP
        parent_LRP = x[_BONUS_PV]
        # children_LRP = children[_BONUS_LRP].sum() if not children.empty else 0
        children_PV = children[_BONUS_PV].sum() if not children.empty else 0

        # Учет OV (для новичков)
        # parent_PV = x[_BONUS_PV] if x['FLAG_NEWCOMER'] == 1 else 0
        # children_PV_ = children.apply(lambda y: y[_BONUS_PV] if y['FLAG_NEWCOMER'] == 1 else 0,
        #							 axis=1).sum() if not children.empty else 0

        # Учет излишка OV (в случае активного FLAG_3_CHILDREN_100)
        # parent_PV_excess = x[_BONUS_PV] - x[_BONUS_LRP] if x['FLAG_3_CHILDREN_100'] > 0 else 0
        # children_PV_excess = children.apply(lambda y: y[_BONUS_PV] - y[_BONUS_LRP] if y['FLAG_PENALTY'] == 1 else 0,
        #									axis=1).sum() if (not children.empty) and (
        #		x['FLAG_3_CHILDREN_100'] > 0) else 0

        res = parent_LRP + children_PV
        return res

    def check_altogether_600(x):
        if x[_BONUS_LEVEL] == 3:
            return 0
        vOV = x[_BONUS_OV]
        res = 1 if vOV >= 600 else 0
        return res

    def check_bonus_50(x):
        res = 1 if (x['FLAG_PARENT_100'] > 0) & (x['FLAG_3_CHILDREN_100'] > 0) & (x['FLAG_ALTOGETHER_600'] > 0) else 0
        res = res * x['FLAG_3_CHILDREN_100']
        return res

    def check_bonus_250(x, src):
        if x[_BONUS_LEVEL] == 3:
            return 0

        children = src[src[_SPONSOR_ID] == x[_ID]]
        if children.empty:
            return 0

        v50 = children.apply(check_bonus_50, axis=1)

        # res = 1 if v50.sum() >= 3 else 0
        res = v50.sum() // 3
        return res

    def check_bonus_1500(x, src):
        if x[_BONUS_LEVEL] == 3:
            return 0

        children = src[src[_SPONSOR_ID] == x[_ID]]
        if children.empty:
            return 0

        v250 = children.apply(lambda x: check_bonus_250(x, src), axis=1)

        # res = 1 if v250.sum() >= 3 else 0
        res = v250.sum() // 3
        return res

    def check_penalty(x):
        res = 1 if x[_BONUS_PV] > x[_BONUS_LRP] else 0
        return res

    def check_newcomer(x):
        date_bonus = _date
        try:
            date_signup = datetime.datetime.strptime(x[_SIGNUP_DATE], "%d.%m.%Y")
        except:
            return 0
        else:
            res = 1 if (date_bonus.month == date_signup.month) and (date_bonus.year == date_signup.year) else 0
            return res

    def get_bonus(x):
        # if x['FLAG_BONUS_1500'] > 0:
        #    res = 1500.0
        # elif x['FLAG_BONUS_250'] > 0:
        #    res = 250.0
        # elif x['FLAG_BONUS_50'] > 0:
        #    res = 50.0
        # else:
        #    res = 0.0
        hi = x['FLAG_BONUS_1500'] * 1500.0
        mi = x['FLAG_BONUS_250'] - x['FLAG_BONUS_1500']
        lo = x['FLAG_BONUS_50'] - x['FLAG_BONUS_1500']

        if mi != 0:
            res = hi + 250.0
        elif lo != 0:
            res = hi + 50.0
        else:
            res = hi

        if x['OV'] < 600:
            res = 0

        return res

    def calculate_bonus(x):
        # Пусть x - строка с лидером 1 уровня
        y = x.copy()
        # Расчет бонуса
        y.loc[:, 'FLAG_PENALTY'] = y.apply(check_penalty, axis=1)
        y.loc[:, 'FLAG_NEWCOMER'] = y.apply(check_newcomer, axis=1)
        y.loc[:, 'FLAG_PARENT_100'] = y.apply(check_parent_100, axis=1)
        y.loc[:, 'FLAG_3_CHILDREN_100'] = y.apply(lambda z: check_3_children_100(z, y), axis=1)
        y.loc[:, _BONUS_OV] = y.apply(lambda z: calculate_ov(z, y), axis=1)
        y.loc[:, 'FLAG_ALTOGETHER_600'] = y.apply(check_altogether_600, axis=1)
        y.loc[:, 'FLAG_BONUS_50'] = y.apply(check_bonus_50, axis=1)
        y.loc[:, 'FLAG_BONUS_250'] = y.apply(lambda z: check_bonus_250(z, y), axis=1)
        y.loc[:, 'FLAG_BONUS_1500'] = y.apply(lambda z: check_bonus_1500(z, y), axis=1)
        y.loc[:, _BONUS_USD] = y.apply(get_bonus, axis=1)
        return y

    def display_scoreboard(x):
        # Пусть x - исходная таблица
        # y - таблица, выводимая в Excel; флаги нужны для дополнительного форматирования
        return x.iloc[:, 0:5].reset_index(drop=True)

    def check_bonus_status(x, src):
        sel = src[src[_SPONSOR_ID] == x[_ID]]
        team_check = True if len(sel) >= 3 else False
        y = x.copy()
        y['TEAM'] = team_check
        # y['QTY'] = len(sel)
        return y

    def rearrange_score(x, src):
        sel = src[src[_SPONSOR_ID] == x[_ID]]
        res = pd.concat([x.to_frame().T,
                         pd.concat(sel.apply(lambda y: pd.concat([y.to_frame().T,
                                                                  src[src[_SPONSOR_ID] == y[_ID]]]), axis=1).tolist())
                         ]) if not sel.empty else x.to_frame().T
        return res

    def set_cell_style(x, row, col, isrc, src, ind):
        # x - строка в фрейме
        # Формат заголовка
        # print_l(f'row = {row}, col = {col}')
        if src.iloc[0, :].name == isrc:
            label = [pygsheets.Cell((row - 1, col + i)) for i in range(6)]
            lbl_val_ = src.columns.values

            for i, c in enumerate(label):
                c.value = lbl_val_[i]
                c.set_text_format('bold', True)

            label[0].value = ''
            label[1].value = label[1].value + ' ' + str(ind + 1)
            CL.extend(label)

        # Формат тела
        line = [pygsheets.Cell((row, col + i)) for i in range(6)]
        values_ = src.loc[isrc, :].tolist()
        values = [i.item() if not isinstance(i, (str, int, float)) else i for i in values_]
        # create note
        note_text = f'Рекрутер: {x[_RECRUITER_ID]} {x[_RECRUITER_NAME]}\nСпонсор: {x[_SPONSOR_ID]} {x[_SPONSOR_NAME]}\nДата последнего заказа: {x[_LAST_ORDER_DATE]}\n'
        note_phones = ''
        for phone in (x[_PHONE], x[_CELL_PHONE], x[_WORK_PHONE]):
            if phone:
                note_text += f'{phone} Whatsapp/Telegram\n'
        # line[1].note = note_text
        for i, c in enumerate(line):
            c.value = values[i]
            if x[_BONUS_LEVEL] != 3:
                if x[_BONUS_LEVEL] == 2:
                    c.set_text_format('bold', True)
                else:
                    c.set_text_format('bold', True).set_text_format('fontSize', 12)
            else:
                c.set_text_format('bold', False)
            if (i != 0) and (i != 5):
                if (x[_BONUS_LEVEL] == 0) or (x[_BONUS_LEVEL] == 1):
                    c.color = LEVEL1.color
                elif x[_BONUS_LEVEL] == 2:
                    c.color = LEVEL2.color
                elif x[_BONUS_LEVEL] == 3:
                    c.color = LEVEL3.color
                else:
                    c.color = EMPTY.color

        if x['FLAG_PARENT_100'] == 1:
            line[2].color = GOOD.color
        elif x['FLAG_PARENT_100'] == 0:
            line[2].color = BAD.color if x['LRP'] != 0 else LEVEL3.color

        if x['FLAG_PENALTY'] == 1:
            line[3].color = WORST.color

        if x['FLAG_NEWCOMER'] == 1:
            line[3].color = GOOD.color

        if x['FLAG_ALTOGETHER_600'] == 1:
            line[4].color = GOOD.color
        elif x['FLAG_ALTOGETHER_600'] == 0:
            if x['OV'] == 0:
                line[4].color = LEVEL3.color
                line[4].value = ""
            else:
                line[4].color = BAD.color

        CL.extend(line)

    def sub_leader_bonus(lead_row: pd.Series):
        ID_ = lead_row['ID']
        lemail = lead_row['Email']
        if pd.isna(lead_row['URL']):
            print("URL не найден, пропуск")
            return
        try:
            bonus_sh = google_sheets_api.open_by_url(lead_row['URL'])
        except:
            print(f"Некорректная ссылка для лидера {ID_} - {lead_row['URL']}")
            raise ValueError(f"Некорректная ссылка для лидера {ID_} - {lead_row['URL']}")
        bonus_worksheets = bonus_sh.worksheets()
        sheet_titles = [sheet.title for sheet in bonus_worksheets]
        bonus_page_title = f"Бонусы {_date.strftime('%m.%y')}"
        # bonus_sh.del_worksheet(bonus_sh.worksheet_by_title('Бонусы')) if 'Бонусы' in wk_titles else None
        if not bonus_page_title in sheet_titles:
            bonus_sh.add_worksheet(bonus_page_title, index=offovrd)
        bonus_wk = bonus_sh.worksheet_by_title(bonus_page_title)
        team_df = team_sheet.get_as_df(empty_value=np.nan)
        MINUS_LEVEL = team_df[team_df['ID'] == ID_].iloc[0]['Уровни']

        # wkTeam = team_sheet[WKSHEETS[0]]

        # Создание иерархии на базе таблицы (до 3 уровня)
        print_l('Строим иерархию...')
        team_dfTrunc = dateExtract(team_df)
        team_dfTrunc['Уровни'] = team_dfTrunc['Уровни'].apply(lambda x: x - MINUS_LEVEL)
        team_dfTrunc = team_dfTrunc[team_dfTrunc['Уровни'] > -1].reset_index(drop=True)
        leader_tree = team_dfTrunc.loc[team_dfTrunc[_LEVELS] == 0].loc[team_dfTrunc['ID'] == ID_].reset_index(drop=True)

        leader_tree.loc[:, ['SUB']] = leader_tree.apply(lambda x: get_subleaders(x, team_dfTrunc), axis=1)

        print_l(
            f'===== РАСЧЕТ БОНУСОВ ДЛЯ ЛИДЕРА {leader_tree.iloc[0, :][_FNAME]} {leader_tree.iloc[0, :][_NAME]}'
            f' ({leader_tree.iloc[0, :][_ID]}) =====')
        print_l(f'Берутся данные за {_date_str}')

        print_l('Составляем таблицу очков...')
        # Очки для головного лидера
        score_board_0 = leader_tree.apply(get_scoreboard, axis=1)

        # Очки для лидеров 1 уровня
        leader_1 = leader_tree['SUB'].values[0].apply(get_leader_with_subs, axis=1)
        score_board_1 = leader_1.apply(lambda x: x.apply(get_scoreboard, axis=1))

        # Расчет бонуса
        print_l('Рассчитываем бонус...')
        sb = pd.concat([score_board_0, pd.concat(score_board_1.values)])
        sbFull = calculate_bonus(sb).reset_index(drop=True)
        # print(sbFull)

        print_l('Разбиваем и форматируем таблицы лидеров...')
        # ===== НУЛЕВОЙ УРОВЕНЬ =====
        lvl0 = sbFull[sbFull[_BONUS_LEVEL] == 0]

        # Зарисовка в таблицу bonus_wk
        gcursor = {'row': 1, 'col': 1}
        cur_lvl = display_scoreboard(lvl0)

        # Чистка таблицы с бонусами
        drange = pygsheets.datarange.DataRange(start='A1', worksheet=bonus_wk)
        drange.clear()
        drange.apply_format(EMPTY)
        global CL
        # Список ячеек на заполнение
        CL = [pygsheets.Cell((1, 4 + cur_lvl.shape[1]),
                             val='Период').set_text_format('bold', True), pygsheets.Cell((2, 4 + cur_lvl.shape[1]),
                                                                                         val=_date_str),
              pygsheets.Cell((1, 11 + cur_lvl.shape[1]),
                             val='Дата генерации').set_text_format('bold', True),
              pygsheets.Cell((2, 11 + cur_lvl.shape[1]),
                             val=datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))]

        # Заполнение заголовка

        # Условная закраска
        lvl0.apply(lambda x: set_cell_style(x, gcursor['row'] + int(x.name) + 1, gcursor['col'], x.name, lvl0, -1),
                   axis=1)

        # ===== ВСЕ ОСТАЛЬНЫЕ УРОВНИ =====
        lvl1 = sbFull[sbFull[_BONUS_LEVEL] != 0].reset_index(drop=True).apply(
            lambda x: check_bonus_status(x, sbFull), axis=1)
        dfSpace = pd.DataFrame([[''] * len(lvl1.columns)], columns=lvl1.columns)

        print_l('Сортируем лидеров по очкам...')
        # Сортировка
        lvl1s = lvl1.sort_values(by=['TEAM', _BONUS_USD, _BONUS_OV, _BONUS_PV, _BONUS_LRP], ascending=False)
        lvl1s = pd.concat(
            lvl1s[lvl1s[_BONUS_LEVEL] == 1].apply(lambda x: rearrange_score(x, lvl1s), axis=1).tolist())

        dfOnes = pd.concat(lvl1s.apply(
            lambda x: pd.concat(
                [dfSpace, x.to_frame().T], ignore_index=True
            ) if x[_BONUS_LEVEL] == 1 else x.to_frame().T, axis=1
        ).values, ignore_index=True).iloc[1:, :]
        dfListOnes = np.split(dfOnes, dfOnes[dfOnes.eq("").all(1)].index)
        dfFrameOnes = [
            i[i.apply(lambda x: x != '')].dropna(how='all').fillna('') for i in dfListOnes
        ]

        dfFrameAll = [
            pd.concat(i.apply(
                lambda x: pd.concat(
                    [dfSpace, x.to_frame().T], ignore_index=True
                ) if x[_BONUS_LEVEL] == 2 else x.to_frame().T, axis=1
            ).values, ignore_index=True) for i in dfFrameOnes]

        print_l('Собираем таблицы с бонусами...')
        colMul = len(dfFrameOnes)
        rowMul = 0
        for ind, fra in enumerate(dfFrameAll):
            # Зарисовка в таблицу bonus_wk
            print_l(f'>>> Обработка таблицы {ind + 1} из {len(dfFrameOnes)}')
            gcursor = {'row': 4, 'col': 1 + 7 * ind}
            cur_lvl = display_scoreboard(fra)
            if len(fra) > rowMul:
                rowMul = len(fra)
            # Условная закраска
            fra.apply(
                lambda x: set_cell_style(x, gcursor['row'] + int(x.name) + 1, gcursor['col'], x.name, fra, ind),
                axis=1)

        print_l('Загружаем таблицы в Google...')
        bonus_wk.rows = rowMul + 5
        bonus_wk.cols = colMul * 7
        bonus_wk.update_cells(CL)
        bonus_wk.adjust_column_width(1, bonus_wk.cols)
        for c_index in range(1, colMul + 1):
            bonus_wk.adjust_column_width(c_index * 7, pixel_size=15)
        bonus_sh.update_properties()
        print_l('Таблица бонусов успешно загружена.')

    # print_l('Проверяем наличие ведомых лидеров...')
    # leader_scanner({'Лидеры': team_worksheet})

    # ===== ОСНОВНОЕ ТЕЛО ПРОГРАММЫ =====
    try:
        offs = int(_bonus['month_offset'])
        offovrd = int(_bonus['month_override'])
        bo = int(_bonus['bonus_only'])

        # Расчет даты (на основе сдвига month_offset и флага month_override)
        if offovrd:
            offs = int(_bonus['month_offset'])
        else:
            day_today = current_date.day
            if day_today in [i + 1 for i in range(12)]:
                offs = 1
            else:
                offs = 0
        if DEMO_MODE:
            offs = int(_bonus['demo_offset'])

        if offs == 0:
            _date = current_date
        else:
            _date = current_date
            for i in range(offs):
                _date = _date.replace(day=1) - datetime.timedelta(days=1)

        _date_str = _date.strftime("%B %Y")
        sub_leader_bonus(leader_row)
        if not pd.isna(leader_row['URL']):
            spreadsheet_processing(google_sheets_api.open_by_url(leader_row['URL']))
        print_l('===== ===== ===== ===== =====')

    except:
        print(traceback.format_exc())
        ERRSTACK.append(
            [f'Google - Расчет бонуса (ИД {leader_row["ID"]}, Уровень {LEVEL})',
             f'Невозможно рассчитать бонус.',
             traceback.format_exc()])
        print(f'Google - Расчет бонуса (ИД {leader_row["ID"]}, Уровень {LEVEL})', '\n', f'Невозможно рассчитать бонус.')
        print(f'===== [#ERROR] Невозможно рассчитать бонус. Пропускаем... =====')


def spreadsheet_processing(spreadsheet: pygsheets.Spreadsheet, core=False):
    try:
        worksheets_titles = [x.title for x in spreadsheet.worksheets()]
        if "Лидеры" not in worksheets_titles:
            print("Лист Лидеры не найден. Пропускаем..")
            return
        leaders_sheet = spreadsheet.worksheet_by_title('Лидеры')
        for column_name, column_letter in [
            ('Имя', 'A'), ('ID', 'B'), ('DT_pass', 'C'), ('SBID', 'D'), ('URL', 'E'), ('Обновление', 'F'),
            ('Prefix', 'G'), ('К-во', 'H'), ('Baikal', 'I'), ('Baikal_user', 'J'), ('Baikal_pass', 'K'),
            ('Файл', 'L'), ('Листы', 'M'), ('Email', 'N'), ('Доступ', 'O'), ('mobileconfig', 'P'),
            ('Pub spreadsheet', 'Q')
        ]:
            if column_name not in leaders_sheet.get_value(f'{column_letter}1'):
                leaders_sheet.update_value(f'{column_letter}1', column_name)

        spreadsheet = google_sheets_api.open_by_url(spreadsheet.url)
        leaders_sheet = spreadsheet.worksheet_by_title('Лидеры')

        leaders_df = leaders_sheet.get_as_df(empty_value=np.nan)

        if core:
            for index, leader_row in leaders_df.iterrows():
                # if get_update_time_bonus_lider(leader_row) == False:
                if not pd.isna(leader_row['URL']):
                    sub_leaders_spreadsheet = google_sheets_api.open_by_url(leader_row['URL'])
                    team_sheet = sub_leaders_spreadsheet.worksheet_by_title('Команда')
                    bonus_processing(leader_row, team_sheet, get_date_from_team_sheet(team_sheet))
                else:
                    print("URL не найден, пропускаем")

        else:
            if 'Команда' not in worksheets_titles:
                print("Лист Команда не найден. Пропускаем")
                return
            team_sheet = spreadsheet.worksheet_by_title('Команда')
            column_z_value = team_sheet.get_col(26, include_tailing_empty=False)[0]

            for index, leader_row in leaders_df.iterrows():
                bonus_processing(leader_row, team_sheet, get_date_from_team_sheet(team_sheet))

        process_public_bonus_sheets(spreadsheet)

    except Exception:
        print(traceback.format_exc())
        ERRSTACK.append([
            f'Google - Обработка таблицы (URL {spreadsheet.url}, Уровень {LEVEL})',
            f'Невозможно обработать таблицу.',
            traceback.format_exc()
        ])
        print(f'Google - Обработка таблицы (URL {spreadsheet.url}, Уровень {LEVEL})', '\n',
              f'Невозможно обработать таблицу.')
        print(f'===== [#ERROR] Невозможно рассчитать бонус. Пропускаем... =====')


def get_date_from_team_sheet(team_wk):
    column_z_value = team_wk.get_col(26, include_tailing_empty=False)[0]
    month, year = column_z_value[3:].split('.')
    *args, num_days = calendar.monthrange(int(year), int(month))
    datetime_now = datetime.datetime(int(year) + 2000, int(month), num_days)
    return datetime_now


def process_public_bonus_sheets(leader_spreadsheet: pygsheets.Spreadsheet):
    leaders_sheet = leader_spreadsheet.worksheet_by_title('Лидеры')
    leaders_df: pd.DataFrame = leaders_sheet.get_as_df(empty_value="")

    if not len(leaders_df):
        return

    try:
        for index, leader_row in leaders_df.iterrows():
            if not leader_row["URL"]:
                continue

            subleader_spreadsheet = google_sheets_api.open_by_url(leader_row["URL"])
            new_public_spreadsheet_title = f"{subleader_spreadsheet.title} Public"

            print_l(f"Публикация листов с бонусом из таблицы {subleader_spreadsheet.title}")

            public_spreadsheet_url = leader_row["Pub spreadsheet"]
            if public_spreadsheet_url:
                public_spreadsheet = google_sheets_api.open_by_url(public_spreadsheet_url)
                public_spreadsheet.title = new_public_spreadsheet_title
                print_l("Публичная таблица открыта")

            else:
                public_spreadsheet = create_public_spreadsheet(new_public_spreadsheet_title)
                leaders_df.at[index, "Pub spreadsheet"] = public_spreadsheet.url
                print_l("Публичная таблица создана")

            publish_bonus_sheets(subleader_spreadsheet, public_spreadsheet)

            if leader_row["SBID"]:
                send_bonus_public_page_link_to_salebot(leader_row["SBID"], public_spreadsheet.id)
                print_l("Ссылка на опубликованную страницу отправлена в salebot")

    finally:
        dt_crm_app.upload_leaders_to_gsheets(leader_spreadsheet, leaders_df)


def create_public_spreadsheet(title: str) -> pygsheets.Spreadsheet:
    try:
        public_folder = google_drive_wrapper.list(
            q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{BONUS_PUBLIC_FOLDER_NAME}'"
        )[0]
    except:
        print_l(f'! Невозможно опубликовать таблицу бонусов {traceback.format_exc()}')
        return

    public_spreadsheet = google_sheets_api.create(title)
    google_sheets_api.drive.move_file(public_spreadsheet.id, "", public_folder["id"])

    google_drive_wrapper.service.revisions().update(
        fileId=public_spreadsheet.id,
        revisionId="1",
        body={
            "published": True,
            "publishAuto": True
        }
    )

    return public_spreadsheet


def publish_bonus_sheets(
        subleader_spreadsheet: pygsheets.Spreadsheet,
        public_spreadsheet: pygsheets.Spreadsheet
):
    # Названия листов, которые нужно опубликовать
    current_datetime = datetime.datetime.now()
    bonus_sheet_title = [
        (current_datetime.replace(day=1) - datetime.timedelta(days=i)).strftime('Бонусы %m.%y')
        for i in range(int(_bonus["publish_months"]))
    ]

    # Получаем листы, которые нужно опубликовать
    sheets_to_publish = []
    for bonus_sheet_title in bonus_sheet_title:
        try:
            sheets_to_publish.append(subleader_spreadsheet.worksheet_by_title(bonus_sheet_title))
        except:
            continue

    if not sheets_to_publish:
        print_l(f"Не найдено листов с бонусом для публикации в таблице {subleader_spreadsheet.title}")
        return

    # Удаляем текущие опубликованные листы
    current_public_sheets = public_spreadsheet.worksheets()
    for sheet in current_public_sheets[1:]:
        public_spreadsheet.del_worksheet(sheet)

    # Оставляем один и переименовываем, потому что нельзя удалить из таблицы все листы
    current_public_sheets[0].title = "_"

    for n, sheet_to_publish in enumerate(sheets_to_publish, 1):
        print_l(f"Публикация листа {n} из {len(sheets_to_publish)}")
        public_sheet = sheet_to_publish.copy_to(public_spreadsheet.id)
        public_sheet.title = sheet_to_publish.title

    # Удаляем последний старый лист
    public_spreadsheet.del_worksheet(current_public_sheets[0])


def send_bonus_public_page_link_to_salebot(client_id: str, spreadsheet_id: str):
    salebot_api.save_variables(int(client_id), {
        _salebot["bonus_publish_url_variable"]: f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/pubhtml"
    })


# функция проверяющая время обновления данных в таблице
def get_update_time_bonus_leader(leader):
    lnow = datetime.datetime.now()

    refresh_time = int(_dt['dt_refresh_time'])

    try:
        ldate = datetime.datetime.strptime(leader['Обновление'], "%d.%m.%Y %H:%M")
    except:
        print_l('Невозможно прочесть дату обновления. Обновляем запись лидера...')
        print_l('Текущее время: ' + lnow.strftime("%d.%m.%Y %H:%M"))
        ldelta = datetime.timedelta(hours=42)
    else:
        ldelta = lnow - ldate
        print_l('Текущее время: ' + lnow.strftime("%d.%m.%Y %H:%M"))
        print_l('Время обновления: ' + ldate.strftime(
            "%d.%m.%Y %H:%M") + f' ({round(ldelta.days * 24 + ldelta.seconds / 3600, 1)} ч. назад)')

    try:
        if ldelta < datetime.timedelta(hours=refresh_time):
            print_l(f'Запись уже обновлялась в течение последних {refresh_time} часов. Пропускаем...')
            return True
    except:
        return False


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

if __name__ == '__main__':
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

    # Загрузка конфигурации
    sourceRes = configparser.ConfigParser()
    sourceRes.read(config, encoding='utf-8')

    _dt = sourceRes['doTERRA']
    _gs = sourceRes['Google']
    _email = sourceRes['E-mail']
    _bonus = sourceRes['Bonus']
    _salebot = sourceRes['SaleBot']

    print('Подключаемся к Google Таблицам...')
    google_sheets_api = pygsheets.authorize(client_secret='clsedtr.json')
    print('Авторизация завершена.')

    google_drive_wrapper = google_sheets_api.drive

    salebot_api = SalebotApi(_salebot["sb_api_key"])

    if not DEMO_MODE:
        core_sheet, core_worksheet = load_google_sheet(_gs['core_key'], core=True, bonus_only=_bonus['bonus_only'])
        spreadsheet_processing(core_sheet, core=True)
        _bonus['month_override'] = '1'
        spreadsheet_processing(core_sheet, core=True)
    else:
        print("==================================")
        print("===== ДЕМОНСТРАЦИОННЫЙ РЕЖИМ =====")
        print("==================================")
        demo_sh, demo_wk = load_google_sheet(_gs['demo_key'], core=True, bonus_only=_bonus['bonus_only'])
        spreadsheet_processing(demo_sh, core=True)
    send_mail(errstack=ERRSTACK, success=True)
    print_l('Работа успешно завершена!')

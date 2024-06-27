import telebot
from telebot import types
from datetime import datetime
import psycopg2


# https://t.me/menu7854125bot
bot = telebot.TeleBot('6643565169:AAFxaHlFbhszpHgxJfm-9gOiBHlXJ_iN4-g')
# Сохранение предыдущего call-хендлера
previous_call = ''

DBNAME = 'postgres'
USER = 'postgres'
PASSWORD = '1a2s3d4f'
HOST = '127.0.0.1'
PORT = '5432'


@bot.message_handler(commands=['start'])
def start(message):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
        with con.cursor() as cur:
            cur.execute('INSERT INTO cafe_users (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING', (message.from_user.id, message.from_user.full_name))
    bot.send_message(message.chat.id, f'Приветствуем Вас, {message.from_user.full_name}, в меню нашего кафе)', reply_markup=get_keyboard('main'))



def generate_message(button):
    if button[1] == '' or button[3] == '':
        raise TypeError('Не указана цена или название')
    msg = f'<b>Блюдо: {button[1]}\n</b>'
    if button[4] != '':
        msg += f'<b>Размер порции: {button[4]}\n\n</b>'
    if button[6] != '':
        msg += button[6] + '\n\n'
    msg += f'<b>Цена: {button[3]} BYN</b>'
    return msg


def get_keyboard(keyboard_name):
    config_data = ''
    keyboard = types.InlineKeyboardMarkup()
    if keyboard_name == 'main':
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
            with con.cursor() as cur:
                cur.execute('SELECT name, next_keyboard FROM cafe_menu_categories')
                config_data = cur.fetchall()
        for button in config_data:
            keyboard.add(types.InlineKeyboardButton(button[0], callback_data=button[1]))
    else:
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
            with con.cursor() as cur:
                cur.execute('SELECT id, name FROM cafe_menu_meals WHERE category = %s', (keyboard_name,))
                config_data = cur.fetchall()
        for button in config_data:
            keyboard.add(types.InlineKeyboardButton(button[1], callback_data=button[0]))
        keyboard.add(types.InlineKeyboardButton('Домой', callback_data='home'))
    return keyboard


@bot.message_handler(content_types=['text'])
def handle_message(message):
    admin_enter = ''
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
        with con.cursor() as cur:
            cur.execute('SELECT * FROM cafe_admin')
            admin_enter = cur.fetchone()[0]
    if message.text != admin_enter:
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
            with con.cursor() as cur:
                cur.execute('INSERT INTO cafe_messages (message, user_id, date) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING', (message.text, message.from_user.id, datetime.now().astimezone().replace(microsecond=0)))
    else:
        bot.send_message(message.chat.id, 'Добро пожаловать в админскую панель', reply_markup=admin_panel())


def admin_panel():
    keyboard = types.InlineKeyboardMarkup()
    buttons = ['Топ 5 блюд по количеству нажатий', 'Топ 10 самых активных пользователей', 'Ссылка на базу данных']
    for button in buttons:
        keyboard.add(types.InlineKeyboardButton(button, callback_data=button))
    return keyboard


def statistics_buttons(call, *category):
    if previous_call == 'Топ 10 самых активных пользователей':
        if call.data in ['По горячим блюдам', "По десертам", "По выпечке", "По напиткам"]:
            bot.send_message(chat_id=call.message.chat.id, text=statistics_users_category2(call, category), reply_markup=admin_panel(), parse_mode='html')
    else:
        if call.data in ['По горячим блюдам', "По десертам", "По выпечке", "По напиткам"]:
            all_buttons = []
            with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
                with con.cursor() as cur:
                    cur.execute('SELECT name, clicks FROM cafe_menu_meals WHERE category = %s ORDER BY clicks DESC LIMIT 5', (category,))
                    all_buttons = cur.fetchall()
            bot.send_message(chat_id=call.message.chat.id, text=category_statistics_buttons2(all_buttons, call.data), reply_markup=admin_panel(), parse_mode='html')
        else:
            all_buttons = []
            with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
                with con.cursor() as cur:
                    cur.execute('SELECT name, clicks FROM cafe_menu_meals ORDER BY clicks DESC LIMIT 5')
                    all_buttons = cur.fetchall()
            message = f'<b>Пятёрка популярных блюд по количеству запросов:</b>\n\n'
            for button in all_buttons:
                message += f'<b>{button[0]}</b>:  {button[1]}\n'
            message += f'\nПо категориям:'
            bot.send_message(chat_id=call.message.chat.id, text=message, reply_markup=category_statistics_buttons(), parse_mode='html')


def category_statistics_buttons2(all_meals, call_data):
    message = f'<b>Пятёрка популярных блюд {call_data.lower()}:</b>\n\n'
    for meal in all_meals:
        message += f'<b>{meal[0]}</b>:  {meal[1]}\n'
    return message


def category_statistics_buttons():
    keyboard = types.InlineKeyboardMarkup()
    buttons = ['По горячим блюдам', "По десертам", "По выпечке", "По напиткам"]
    for button in buttons:
        keyboard.add(types.InlineKeyboardButton(button, callback_data=button))
    return keyboard



def statistics_users_category(call):
    ten = []
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
        with con.cursor() as cur:
            cur.execute('SELECT COUNT(cafe_clicks.user_id), cafe_users.id, cafe_users.name FROM cafe_clicks INNER JOIN cafe_users ON cafe_clicks.user_id = cafe_users.id GROUP BY cafe_users.name, cafe_users.id LIMIT 10')
            ten = cur.fetchall()
    message = f'Десятка самых активных пользователей по количеству запросов:\n\n'
    for user in ten:
        message += f'<b>{user[2]}</b> ({user[1]}):   {user[0]}\n'
    message += f'\nПо категориям:'
    bot.send_message(chat_id=call.message.chat.id, text=message, reply_markup=category_statistics_buttons(), parse_mode='html')


def statistics_users_category2(call, category):
    message = f'Десятка самых активных пользователей "{call.data.lower()}":\n\n'
    users = {}
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
        with con.cursor() as cur:
            cur.execute('SELECT  COUNT(cafe_clicks.user_id), cafe_users.id, cafe_users.name FROM cafe_clicks  INNER JOIN cafe_users ON cafe_clicks.user_id = cafe_users.id INNER JOIN cafe_menu_meals ON cafe_clicks.click = cafe_menu_meals.name WHERE cafe_menu_meals.category = %s GROUP BY cafe_users.name, cafe_users.id LIMIT 10', (category,))
            users = cur.fetchall()
    for user in users:
        message += f'<b>{user[2]}</b> ({user[1]}):  {user[0]}\n'
    return message


@bot.callback_query_handler(func=lambda call: True)
def common_button(call):
    if call.data == 'home':
        bot.send_message(chat_id=call.message.chat.id, text=f'Вы вернулись в главное меню', reply_markup=get_keyboard('main'))
    elif call.data in ['hot_meals', 'dessert_meals', 'drinks', 'bakery']:
        try:
            config_data = ''
            with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
                with con.cursor() as cur:
                    cur.execute('SELECT description FROM cafe_menu_categories WHERE next_keyboard = %s', (call.data,))
                    config_data = cur.fetchone()
            bot.send_message(
                chat_id=call.message.chat.id,
                text=config_data[0],
                reply_markup=get_keyboard(call.data),
                parse_mode='html'
            )
        except:
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Что-то пошло не так...',
                reply_markup=get_keyboard('main'),
                parse_mode='html'
            )

    elif call.data =='Топ 5 блюд по количеству нажатий':
        statistics_buttons(call)
    elif call.data =='Топ 10 самых активных пользователей':
        statistics_users_category(call)
    elif call.data =='Ссылка на базу данных':
        bot.send_message(chat_id=call.message.chat.id, text='https://console.firebase.google.com/project/program-c37c4/firestore/databases/-default-/data/~2Fcafe', reply_markup=admin_panel())
    elif call.data == 'По горячим блюдам':
        statistics_buttons(call,'hot_meals')
    elif call.data == 'По десертам':
        statistics_buttons(call,'dessert_meals')
    elif call.data == 'По выпечке':
        statistics_buttons(call,'bakery')
    elif call.data == 'По напиткам':
        statistics_buttons(call,'drinks')
    else:
        button = ''
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT) as con:
            with con.cursor() as cur:
                cur.execute('SELECT * FROM cafe_menu_meals WHERE id = %s', (call.data,))
                button = cur.fetchone()
                cur.execute('UPDATE cafe_menu_meals SET clicks=clicks + 1 WHERE id = %s', (call.data,))
                cur.execute('INSERT INTO cafe_clicks (click, user_id, date) VALUES (%s, %s, %s)', (button[1], call.from_user.id, datetime.now().astimezone().replace(microsecond=0)))
        try:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=generate_message(button),
                reply_markup=get_keyboard(button[2]),
                parse_mode='html'
            )
        except:
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Нет данных',
                reply_markup=get_keyboard(button[2]),
            )

    global previous_call
    previous_call = call.data



bot.polling(non_stop=True, interval=0)

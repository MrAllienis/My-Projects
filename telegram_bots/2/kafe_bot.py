import telebot
from telebot import types
import json
from main import firestore_client
from datetime import datetime


# https://t.me/menu7854125bot
bot = telebot.TeleBot('6643565169:AAFxaHlFbhszpHgxJfm-9gOiBHlXJ_iN4-g')
# Сохранение предыдущего call-хендлера
previous_call = ''


@bot.message_handler(commands=['start'])
def start(message):
    document = firestore_client.get_doc('cafe', 'users')
    users_id = set()
    for user in list(document.values())[0]:
        users_id.add(user['id'])
    if message.from_user.id not in users_id:
        document['users'].append({'id': '', 'messages': '', 'name': ''})
        list(document.values())[0][-1]['id'] = message.from_user.id
        list(document.values())[0][-1]['name'] = message.from_user.full_name
        list(document.values())[0][-1]['messages'] = 0
        firestore_client.set_doc('cafe', 'users', document)
    bot.send_message(message.chat.id, f'Приветствуем Вас, {message.from_user.full_name}, в меню нашего кафе)', reply_markup=get_keyboard('main'))




def generate_message(button):
    msg = ''
    if 'size' in button or 'price' in button:
        msg += f'<b>Блюдо: {button["name"]}\n</b>'
    if 'size' in button:
        msg += f'<b>Размер порции: {button["size"]}\n\n</b>'
    if 'to_print' in button:
        msg += button['to_print'] + '\n'

    if 'price' in button:
        msg += f'\n<b>Цена: {button["price"]} BYN</b>'

    return msg


def get_all_buttons():
    document = firestore_client.get_doc('cafe', 'menu')
    config_data = document
    all_buttons = []
    for keyboard in config_data.values():
        for button in keyboard['buttons']:
            all_buttons.append(button)
    return all_buttons


def get_keyboard(keyboard_name):
    document = firestore_client.get_doc('cafe', 'menu')
    config_data = document
    actual_keyboard = list(filter(lambda el: el['keyboard_name'] == keyboard_name, config_data.values()))[0]
    keyboard = types.InlineKeyboardMarkup()
    buttons = sorted(actual_keyboard['buttons'], key=lambda el: int(el['id']))
    for button in buttons:
        keyboard.add(types.InlineKeyboardButton(button['name'], callback_data=button['id']))
    return keyboard


@bot.message_handler(content_types=['text'])
def handle_message(message):
    document = firestore_client.get_doc('cafe', 'messages')
    document_admin = firestore_client.get_doc('cafe', 'admin')
    if message.text != document_admin['admin_panel']:
        document['messages'].append({'message': message.text, 'name': message.from_user.full_name, 'id': message.from_user.id, 'date/time': datetime.now().astimezone()})
        firestore_client.set_doc('cafe', 'messages', document)
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
            document = firestore_client.get_doc('cafe', 'menu')
            config_data = document
            all_buttons = []
            for keyboard in config_data.values():
                if keyboard['keyboard_name'] != 'main':
                    for button in keyboard['buttons']:
                        if button['name'] != 'Домой':
                            all_buttons.append(button)
            all_meals = sorted(all_buttons, key=lambda el: int(el['clicks']), reverse=True)
            bot.send_message(chat_id=call.message.chat.id, text=category_statistics_buttons2(all_meals, call.data, category), reply_markup=admin_panel(), parse_mode='html')
        else:
            document = firestore_client.get_doc('cafe', 'menu')
            config_data = document
            all_buttons = []
            for keyboard in config_data.values():
                if keyboard['keyboard_name'] != 'main':
                    for button in keyboard['buttons']:
                        if button['name'] != 'Домой':
                            all_buttons.append(button)
            five = sorted(all_buttons, key=lambda el: int(el['clicks']), reverse=True)[:5]
            message = f'<b>Пятёрка популярных блюд по количеству запросов:</b>\n\n'
            for f in five:
                message += f'<b>{f["name"]}</b>:  {f["clicks"]}\n'
            message += f'\nПо категориям:'
            bot.send_message(chat_id=call.message.chat.id, text=message, reply_markup=category_statistics_buttons(), parse_mode='html')


def category_statistics_buttons2(all_meals, call_data, category):
    message = f'<b>Пятёрка популярных блюд {call_data.lower()}:</b>\n\n'
    true_meals = []
    for meal in all_meals:
        if category[0] == meal['next_keyboard']:
            true_meals.append(meal)

    for m in true_meals:
        message += f'<b>{m["name"]}</b>:  {m["clicks"]}\n'
    return message


def category_statistics_buttons():
    keyboard = types.InlineKeyboardMarkup()
    buttons = ['По горячим блюдам', "По десертам", "По выпечке", "По напиткам"]
    for button in buttons:
        keyboard.add(types.InlineKeyboardButton(button, callback_data=button))
    return keyboard


def statistics_users():
    document = firestore_client.get_doc('cafe', 'users')
    ten = sorted(list(document.values())[0], key=lambda el: len(el['messages']), reverse=True)[:10]
    message = f'Десятка самых активных пользователей по количеству запросов:\n\n'
    for user in ten:
        message += f'<b>{user["name"]}</b> ({user["id"]}):   {len(user["messages"])}\n'
    message += f'\nПо категориям:'
    return message


def statistics_users_category(call):
    bot.send_message(chat_id=call.message.chat.id, text=statistics_users(), reply_markup=category_statistics_buttons(), parse_mode='html')


def statistics_users_category2(call, category):
    message = f'Десятка самых активных пользователей "{call.data.lower()}":\n\n'
    document = firestore_client.get_doc('cafe', 'users')
    users = {}
    for user in list(document.values())[0]:
        users[user['name']] = [0, user['id']]
        if len(user['messages']) > 0:
            for meal in user['messages']:
                if list(meal.values())[0]['category'] == category[0]:
                    users[user['name']][0] += 1
    users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True)[:10])
    for user in users.items():
        message += f'<b>{user[0]}</b>({user[1][1]}):  {user[1][0]}\n'
    return message


@bot.callback_query_handler(func=lambda call: True)
def common_button(call):
    if call.data =='Топ 5 блюд по количеству нажатий':
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
        button = list(filter(lambda btn: call.data == btn['id'], get_all_buttons()))[0]
        exceptions = ['Домой', 'Горячие блюда', 'Выпечка', 'Напитки', 'Десерты']
        if button['name'] not in exceptions:
            document = firestore_client.get_doc('cafe', 'users')
            for user in list(document.values())[0]:
                if user['id'] == call.from_user.id:
                    user['messages'].append({button['name']:{'date': datetime.now().astimezone(), 'category': button['next_keyboard']}})
                    if len(user['messages']) > 1000:
                        remainder = len(user['messages']) - 1000
                        user['messages'] = user['messages'][remainder:]
            firestore_client.set_doc('cafe', 'users', document)
            document2 = firestore_client.get_doc('cafe', 'menu')
            for dish in list(document2.values()):
                for el in dish['buttons']:
                    if el['id'] == button['id']:
                        el['clicks'] += 1
            firestore_client.set_doc('cafe', 'menu', document2)
        try:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=generate_message(button),
                reply_markup=get_keyboard(button['next_keyboard']),
                parse_mode='html'
            )
        except:
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Нет данных',
                reply_markup=get_keyboard(button['next_keyboard']),
            )
    global previous_call
    previous_call = call.data



bot.polling(non_stop=True, interval=0)

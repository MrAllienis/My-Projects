from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import asyncio


API_TOKEN = '7531137149:AAEyU9nqk0QGYnHX5Pr-dkYf5jcmFxDO3jQ'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
CHANNEL_ID = '-1002202725655'


async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    yclid = ''
    web_app_url = "https://www.skidki186.ru/shops"
    if message.get_args():  # Проверка, есть ли параметры
        yclid = message.get_args()  # Получаем параметр yclid
        web_app_url = "https://www.skidki186.ru/shops" + '?yclid=' + yclid
    if await check_subscription(user_id):
        welcome_text = "👋 Привет! Я помогу сэкономить на твоих покупках.\nВыбери предложение:"
        web_app_button = InlineKeyboardButton(text="Список предложений", web_app=types.WebAppInfo(url=web_app_url))
        keyboard = InlineKeyboardMarkup().add(web_app_button)
        sent_message = await message.answer(welcome_text, reply_markup=keyboard)
        if message.get_args():
            web_app_url = "https://www.skidki186.ru/shops"
            # Ждем 10 секунд перед удалением сообщения
            await asyncio.sleep(60)

            # Создаем новую кнопку и клавиатуру
            new_button = InlineKeyboardButton(text="Список предложений", web_app=types.WebAppInfo(url=web_app_url))
            new_keyboard = InlineKeyboardMarkup().add(new_button)

            # Обновляем существующее сообщение, заменяя текст и клавиатуру
            await bot.edit_message_text(
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id,
                text=welcome_text,
                reply_markup=new_keyboard
            )

    else:
        # Кнопка для подписки на канал
        subscribe_button = InlineKeyboardButton(text="Подписаться на канал ✅", url="https://t.me/+meJdp3-tCTUxZjky")
        check_button = InlineKeyboardButton(text="Я подписался ✅", callback_data=f"check_subscription:{yclid}")
        keyboard = InlineKeyboardMarkup().add(subscribe_button).add(check_button)
        await message.answer("👋 Приветствуем! Чтобы пользоваться промокодами и купонами, Вы должны быть подписаны на наш канал", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('check_subscription:'))
async def process_subscription_check(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    web_app_url = "https://www.skidki186.ru/shops"
    if callback_query.data.split(":")[1]:
        yclid = callback_query.data.split(":")[1]
        web_app_url = "https://www.skidki186.ru/shops" + '?yclid=' + yclid

    if await check_subscription(user_id):
        await bot.answer_callback_query(callback_query.id)
        welcome_text = "🎉 Спасибо за подписку! Теперь выберите предложение:"
        web_app_button = InlineKeyboardButton(text="Список предложений", web_app=types.WebAppInfo(url=web_app_url))
        keyboard = InlineKeyboardMarkup().add(web_app_button)
        sent_message = await bot.send_message(callback_query.from_user.id, welcome_text, reply_markup=keyboard)
        web_app_url = "https://www.skidki186.ru/shops"
        # Ждем 10 секунд перед удалением сообщения
        await asyncio.sleep(60)

        # Создаем новую кнопку и клавиатуру
        new_button = InlineKeyboardButton(text="Список предложений", web_app=types.WebAppInfo(url=web_app_url))
        new_keyboard = InlineKeyboardMarkup().add(new_button)

        # Обновляем существующее сообщение, заменяя текст и клавиатуру
        await bot.edit_message_text(
            chat_id=sent_message.chat.id,
            message_id=sent_message.message_id,
            text="🎉 Спасибо за подписку! Теперь выберите предложение:",
            reply_markup=new_keyboard
        )

    else:
        await bot.answer_callback_query(callback_query.id, text="Вы все еще не подписаны на наш канал.", show_alert=True)


# Функция отправки события в Яндекс Метрику
def send_event_to_yandex_metrika(event_name, user_id):
    metrika_counter_id = '98592826'
    metrika_token = 'y0_AgAAAAB0d-z0AAyVIgAAAAET1WLrAAA0SeuxIqZOlKM6yXvxfuEYdakPGw'

    url = f'https://api-metrika.yandex.net/management/v1/counter/{metrika_counter_id}/event.json'
    headers = {
        'Authorization': f'OAuth {metrika_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "event_name": event_name,
        "user_id": user_id
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Событие успешно отправлено")
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
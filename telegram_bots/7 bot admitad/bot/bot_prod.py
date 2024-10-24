from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

API_TOKEN = '6887289745:AAFqXwtC_QSdAPXW2AguedZsBJ5cmKLTvcQ'
web_app_url = "https://www.skidki186.ru/shops_products"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
CHANNEL_ID = '-1002202725655'


async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Проверяем статус пользователя
        if member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        # Обрабатываем возможные ошибки, например, если канал недоступен
        print(f"Ошибка при проверке подписки: {e}")
        return False


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if await check_subscription(user_id):
        welcome_text = "👋 Привет! Я помогу тебе выбрать товары в нашем каталоге."
        web_app_button = InlineKeyboardButton(text="Открыть каталог", web_app=types.WebAppInfo(url=web_app_url))
        keyboard = InlineKeyboardMarkup().add(web_app_button)
        await message.answer(welcome_text, reply_markup=keyboard)
    else:
        # Кнопка для подписки на канал
        subscribe_button = InlineKeyboardButton(text="Подписаться на канал ✅", url="https://t.me/+meJdp3-tCTUxZjky")
        check_button = InlineKeyboardButton(text="Я подписался ✅", callback_data="check_subscription")
        keyboard = InlineKeyboardMarkup().add(subscribe_button).add(check_button)
        await message.answer("👋 Приветствуем! Чтобы пользоваться каталогом товаров, Вы должны быть подписаны на наш канал", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'check_subscription')
async def process_subscription_check(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_subscription(user_id):
        await bot.answer_callback_query(callback_query.id)
        welcome_text = "🎉 Спасибо за подписку! Теперь можете выбирать товары:"
        web_app_button = InlineKeyboardButton(text="Открыть каталог", web_app=types.WebAppInfo(url=web_app_url))
        keyboard = InlineKeyboardMarkup().add(web_app_button)
        await bot.send_message(callback_query.from_user.id, welcome_text, reply_markup=keyboard)
    else:
        await bot.answer_callback_query(callback_query.id, text="Вы все еще не подписаны на наш канал.", show_alert=True)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
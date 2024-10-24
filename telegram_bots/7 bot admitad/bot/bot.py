import logging
import asyncio
import random
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from message import get_coupons, load_template_coupon, load_template_products, create_message, create_product, get_advcampaigns_for_website2
from db_con import delete_shop, select_from_db, get_image_xlsx, select_products, delete_coupon_from_db, update_used_coupon, delete_old_coupons, select_tasks, update_used_product
from datetime import datetime, timedelta, time



ADMIN_CHAT_ID = [7010151873, 751638794]
API_TOKEN = '7213960854:AAEu2p1xDs5HjaZ5wKpMq2GxZ-9mfPku8zI'
CHANNEL_ID = '-1002210052557'  # Замените на ваш идентификатор канала MY
# CHANNEL_ID = '-1002202725655'  # Замените на ваш идентификатор канала

max_posts_per_day = 355
posts_count = 0
next_reset_time = datetime.combine(datetime.now().date() + timedelta(days=1), time(0, 0))

scheduler = AsyncIOScheduler()


day_time1 = 10
day_time2 = 22

class Form(StatesGroup):
    change_interval = State()
    change_time1 = State()  # State for day_time1
    change_time2 = State() # State for day_time2
    delete_shop = State()
    post = State()
    post_product = State()

interval = 180*60

# Настройка логирования
logging.basicConfig(level=logging.INFO)

stop_event = asyncio.Event()

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

dp.middleware.setup(LoggingMiddleware())
admin_kb = InlineKeyboardMarkup(row_width=1)
btn_post = InlineKeyboardButton('📩 Выбрать промокод для публикации', callback_data='admin_post')
btn_post_prod = InlineKeyboardButton('📩 Выбрать товар для публикации', callback_data='admin_post_product')
btn_stats = InlineKeyboardButton(' ✉️ Опубликовать рандомный пост с промокодом 🎲', callback_data='admin_coupon')
btn_message = InlineKeyboardButton('✉️ Опубликовать рандомный пост с товаром 🎲', callback_data='admin_prod')
btn_users = InlineKeyboardButton('📊 Настроить автоматическую публикацию', callback_data='admin_auto')
btn_delete = InlineKeyboardButton('🗑 Удалить магазин', callback_data='admin_delete_shop')
admin_kb.add(btn_post, btn_post_prod, btn_stats, btn_message, btn_users, btn_delete)


async def on_startup(dispatcher):
    # await bot.send_message(7010151873,'Запуск бота. Восстановление данных... ')
    # try:
    #     messages_for_delete, text = get_coupons()
    #     await bot.send_message(7010151873, text)
    #     for message in messages_for_delete.values():
    #         if (message[0] and message[1]) is not None:
    #             await bot.delete_message(message[0], message[1])
    # except:
    #     print('Нет сообщений для удаления')
    # try:
    #     old_messages = delete_old_coupons()
    #     for mes in old_messages:
    #         try:
    #             await bot.delete_message(mes[0], mes[1])
    #         except:
    #             print('Сообщение не удалено')
    # except Exception as e:
    #     print(f'Ошибка удаления старых сообщений - {e}')
    # try:
    #     tasks_for_delete = select_tasks()
    #     for task in tasks_for_delete:
    #         print(f'Пост будет удален {task[2]}')
    #         asyncio.create_task(delete_post_at(bot, task[0], task[1], task[2], task[3]))
    #     print('Запланированные удаления восстановлены')
    # except Exception as e:
    #     print(f'Ошибка. Запланированные удаления не восстановлены - {e}')
    # try:
    #     products_for_delete, not_rub = get_advcampaigns_for_website2()
    #     for product in products_for_delete:
    #         await bot.delete_message(product[0], product[1])
    #     print(not_rub)
    #
    # except Exception as e:
    #     print('Нет постов с товарами для удаления')
    print('База данных полностью восстановлена, бот готов к работе. База данных будет обновляться каждые 2 часа')
    await bot.send_message(7010151873, 'База данных полностью восстановлена, бот готов к работе. База данных будет обновляться каждые 4 часа')











# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    welcome_text = (
        "Привет! 👋\n\n"
        "Добро пожаловать в нашего бота!"
    )

    await message.answer(welcome_text)



# Обработчик команды /admin
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.chat.id in ADMIN_CHAT_ID:
        await message.answer("Панель администратора:", reply_markup=admin_kb)
    else:
        await message.answer("У вас нет доступа к этой команде.")

# Обработчик нажатий на кнопки в админке
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('admin_'))
async def admin_callback_handler(callback_query: CallbackQuery):
    data = callback_query.data
    if data == 'admin_prod':
        image, message, id = create_product()
        while message == '':
            image, message, id = create_product()
        else:
            await send_product_to_channel(image, message, id)

    elif data == 'admin_coupon':
        image, message, endtime, coupon_id = create_message()
        while message == '':
            image, message, endtime, coupon_id = create_message()
        else:
            await send_message_to_channel(image, message, endtime, coupon_id)

    elif data == 'admin_auto':
        keyboard = schedule_keyboard()
        await bot.send_message(callback_query.from_user.id, text='Выберите опцию:', reply_markup=keyboard)

    elif data == 'admin_delete_shop':
        await Form.delete_shop.set()  # Set the state
        await bot.send_message(callback_query.from_user.id, "Введите название магазина:")

    elif data == 'admin_post':
        await Form.post.set()  # Set the state
        await bot.send_message(callback_query.from_user.id, "Введите название промокода:")

    elif data == 'admin_post_product':
        await Form.post_product.set()  # Set the state
        await bot.send_message(callback_query.from_user.id, "Введите ссылку на товар:")

    else:
        await bot.answer_callback_query(callback_query.id, "Неизвестная команда")




# Обработчик кнопки "Назад"
@dp.callback_query_handler(lambda c: c.data and c.data == 'back')
async def back_callback_handler(callback_query: CallbackQuery):
    await bot.send_message(callback_query.message.chat.id, "Панель администратора:",  reply_markup=admin_kb)
    await bot.answer_callback_query(callback_query.id)



@dp.callback_query_handler(lambda c: c.data == 'start_posts')
async def start_posts_callback(callback_query: types.CallbackQuery):
    stop_event.clear()
    global day_time1, day_time2
    # if day_time1 <= datetime.now().hour+3 < day_time2:
    global interval
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Отправка сообщений каждые {interval/60} минут начата.")
    asyncio.create_task(reset_posts_count_daily())  # Запускаем задачу для сброса счетчика
    asyncio.create_task(start_posts_interval())
    # else:
    #     await bot.send_message(callback_query.from_user.id, f"Отправка сообщений доступна только с {day_time1} до {day_time2} часов.")


@dp.callback_query_handler(lambda c: c.data == 'end_posts')
async def end_posts_callback(callback_query: types.CallbackQuery):
    stop_event.set()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Отправка сообщений остановлена.")




@dp.message_handler(state=Form.delete_shop)
async def process_delete_shop(message: types.Message, state: FSMContext):
    try:
        messages_for_delete = delete_shop(message.text)
        if messages_for_delete is False:
            await message.answer('Такого магазина не существует')
        else:
            await message.answer('Магазин полностью удален из базы')
            for mes in messages_for_delete:
                try:
                    if (mes[0] and mes[1]) is not None:
                        await bot.delete_message(mes[0], mes[1])
                except:
                    pass
            await message.answer('Магазин полностью удален из канала')
    except:
        await message.answer('Ошибка')
    finally:
        await state.finish()



@dp.message_handler(state=Form.post)
async def process_delete_shop(message: types.Message, state: FSMContext):
    try:
        image, post, endtime, coupon_id = create_message(admin_post=message.text)
        await send_message_to_channel(image, post, endtime, coupon_id)
        await message.answer('Промокод опубликован')
    except:
        await message.answer('Промокод не существует. Введите точное название')
    finally:
        await state.finish()


@dp.message_handler(state=Form.post_product)
async def process_delete_shop(message: types.Message, state: FSMContext):
    try:
        image_p, message_p, id = create_product(post_link=message.text)
        await send_product_to_channel(image_p, message_p, id)
        await message.answer('Товар опубликован')
    except:
        await message.answer('Товар не существует. Введите точную ссылку')
    finally:
        await state.finish()




@dp.callback_query_handler(lambda c: c.data == 'change_interval')
async def change_interval_callback(callback_query: types.CallbackQuery):
    await Form.change_interval.set()  # Set the state
    await bot.send_message(callback_query.from_user.id, "Введите новый интервал в минутах:")


# Message handler for processing the interval change
@dp.message_handler(state=Form.change_interval)
async def process_interval(message: types.Message, state: FSMContext):
    try:
        global interval
        interval = int(message.text)*60
        await message.answer(f'Установлен новый примерный интервал на {message.text} минут', reply_markup=schedule_keyboard())
    except ValueError:
        await message.answer('Пожалуйста, введите только число.')
    finally:
        await state.finish()  # Finish the state




@dp.callback_query_handler(lambda c: c.data == 'change_time')
async def change_time_callback(callback_query: types.CallbackQuery):
    await Form.change_time1.set()  # Set the state for day_time1
    await bot.send_message(callback_query.from_user.id, "Укажите значение часа, с которого будет возможна отправка постов:")

# Message handler for processing day_time1
@dp.message_handler(state=Form.change_time1)
async def process_time1(message: types.Message, state: FSMContext):
    global day_time1
    try:
        day_time1 = int(message.text)
        if 1 <= day_time1 < 16:
            await message.answer(f'Установлено значение нижнего порога времени - {day_time1}:00')
            await Form.change_time2.set()  # Set the state for day_time2
            await bot.send_message(message.from_user.id, "Укажите значение часа, до которого будет возможна отправка постов:")
        else:
            await message.answer('Число не может быть больше 15, и меньше 1, попробуйте ещё раз')
    except ValueError:
        await message.answer('Пожалуйста, введите только число.')

# Message handler for processing day_time2
@dp.message_handler(state=Form.change_time2)
async def process_time2(message: types.Message, state: FSMContext):
    global day_time2
    try:
        day_time2 = int(message.text)
        if 23 >= day_time2 >= 16:
            await message.answer(f'Установлено значение верхнего порога времени - {day_time2}:00', reply_markup=schedule_keyboard())
        else:
            await message.answer('Число не может быть меньше 16, и больше 23, попробуйте ещё раз')
    except ValueError:
        await message.answer('Пожалуйста, введите только число.')
    finally:
        await state.finish()  # Finish the state



def schedule_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    interval_button = InlineKeyboardButton('↔️ Изменить интервал отправки постов', callback_data='change_interval')
    start = InlineKeyboardButton('▶️ Запуск отправки постов', callback_data='start_posts')
    end = InlineKeyboardButton('⏸ Остановка отправки постов', callback_data='end_posts')
    time = InlineKeyboardButton('🕰 Изменить разрешенное время для публикации', callback_data='change_time')
    back = InlineKeyboardButton('⬅️ Назад', callback_data='back')
    keyboard.add(start, end, interval_button, time, back)
    return keyboard



# async def periodic_loading():
#     print('Начало парсинга')
#     await bot.send_message(7010151873, 'Парсинг начался')
#
#     try:
#         messages_for_delete = get_coupons()
#         for message in messages_for_delete.values():
#             if (message[0] and message[1]) is not None:
#                 await bot.delete_message(message[0], message[1])
#     except Exception as e:
#         print('Нет сообщений для удаления:', e)
#
#     try:
#         products_for_delete, not_rub = get_advcampaigns_for_website2()
#         for product in products_for_delete:
#             await bot.delete_message(product[0], product[1])
#         print(not_rub)
#     except Exception as e:
#         print('Нет постов с товарами для удаления:', e)
#
#     print('Парсинг завершен')
#     await bot.send_message(7010151873, 'Парсинг завершен')




async def reset_posts_count_daily():
    global posts_count, next_reset_time
    while True:
        # Сброс счетчика в полночь
        now = datetime.now()
        if now >= next_reset_time:
            posts_count = 0
            next_reset_time = datetime.combine(now.date() + timedelta(days=1), time(0, 0))
        await asyncio.sleep(60)  # Проверять каждые 60 секунд



async def delete_post_at(bot, chat_id, message_id, delete_time, coupon_id):
    now = datetime.now().astimezone()
    delay = (delete_time - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id, message_id)
        await delete_coupon_from_db(coupon_id)


async def start_posts_interval():
    global interval, posts_count, day_time1, day_time2
    while not stop_event.is_set():
        if posts_count < max_posts_per_day:
            # if day_time1 <= datetime.now().hour + 3 < day_time2:
            image, message, endtime, coupon_id = create_message()
            while message == '':
                image, message, endtime, coupon_id = create_message()
            await send_message_to_channel(image, message, endtime, coupon_id)
            posts_count += 1  # Увеличиваем счетчик после отправки

            if posts_count >= max_posts_per_day:
                await bot.send_message(7010151873, f"Достигнут дневной лимит отправки сообщений. ({max_posts_per_day})")

        # await asyncio.sleep(interval+(random.randint(-30, 30))*60)
        await asyncio.sleep(10)

        # if posts_count < max_posts_per_day:
        #     # if day_time1 <= datetime.now().hour + 3 < day_time2:
        #     image_p, message_p, id = create_product()
        #     while message_p == '':
        #         image_p, message_p, id = create_product()
        #     await send_product_to_channel(image_p, message_p, id)
        #     posts_count += 1  # Увеличиваем счетчик после отправки
        #
        #     if posts_count >= max_posts_per_day:
        #         await bot.send_message(7010151873, f"Достигнут дневной лимит отправки сообщений. ({max_posts_per_day})")
        #
        # # await asyncio.sleep(interval+(random.randint(-30, 30))*60)
        # await asyncio.sleep(10)

        if posts_count < max_posts_per_day:
            # if day_time1 <= datetime.now().hour + 3 < day_time2:
            image, message, endtime, coupon_id = create_message(promo=True)
            while message == '':
                image, message, endtime, coupon_id = create_message(promo=True)
            await send_message_to_channel(image, message, endtime, coupon_id)
            posts_count += 1  # Увеличиваем счетчик после отправки

            if posts_count >= max_posts_per_day:
                await bot.send_message(7010151873, f"Достигнут дневной лимит отправки сообщений. ({max_posts_per_day})")

        # await asyncio.sleep(interval+(random.randint(-30, 30))*60)
        await asyncio.sleep(10)

async def send_product_to_channel(image, message, id):
    try:
        with open(image, 'rb') as photo:
            msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=message, parse_mode='HTML')
    except Exception as e:
        await asyncio.sleep(10)
        print(e)
        traceback.print_exc()
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML', disable_web_page_preview=True)
    update_used_product(id, CHANNEL_ID, msg.message_id)



async def send_message_to_channel(image, message, endtime, coupon_id):
    try:
        with open(image, 'rb') as photo:
            msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=message, parse_mode='HTML')
    except Exception as e:
        await asyncio.sleep(10)
        print(e)
        traceback.print_exc()
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML', disable_web_page_preview=True)
    update_used_coupon(coupon_id, CHANNEL_ID, msg.message_id)
    if endtime is not None:
        delete_time = endtime
        print(f'Пост будет удален {delete_time}')
        # await bot.send_message(7010151873, f'Пост будет удален {delete_time}')
        # await bot.send_message(751638794, f'Пост будет удален {delete_time}')
        asyncio.create_task(delete_post_at(bot, CHANNEL_ID, msg.message_id, delete_time, coupon_id))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

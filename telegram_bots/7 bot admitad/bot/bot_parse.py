import asyncio
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

from message import get_coupons, get_advcampaigns_for_website2





scheduler = AsyncIOScheduler()

ADMIN_CHAT_ID = [7010151873, 751638794]
API_TOKEN = '7213960854:AAEu2p1xDs5HjaZ5wKpMq2GxZ-9mfPku8zI'

bot = Bot(token=API_TOKEN)



async def periodic_loading():
    print('Начало парсинга')
    # await bot.send_message(7010151873, 'Парсинг начался')

    try:
        messages_for_delete, text, go_out_shops = get_coupons()
        # await bot.send_message(7010151873, text)
        # await bot.send_message(7010151873, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        # await bot.send_message(751638794, text=f'Магазины, которые больше не с нами: {go_out_shops}')
        for message in messages_for_delete.values():
            if (message[0] is not None) and (message[1] is not None):
                await bot.delete_message(message[0], message[1])
    except Exception as e:
        print('Нет сообщений для удаления:', e)

    try:
        products_for_delete, not_rub = get_advcampaigns_for_website2()
        for product in products_for_delete:
            await bot.delete_message(product[0], product[1])
        print(not_rub)
        # await bot.send_message(7010151873, f'Товары не доступны: {not_rub}')
        # await bot.send_message(751638794, f'Товары не доступны: {not_rub}')
    except Exception as e:
        print('Нет постов с товарами для удаления:', e)

    print('Парсинг завершен')
    await bot.send_message(7010151873, 'Парсинг завершен')


if __name__ == '__main__':
    asyncio.run(periodic_loading())
    # loop = asyncio.get_event_loop()
    # scheduler.add_job(periodic_loading, IntervalTrigger(seconds=10))
    # scheduler.start()
    # loop.run_forever()
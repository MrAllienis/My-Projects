# pip install aiogram
# pip install gTTS
# pip install deep-translator
# root@45.135.234.66
# nohup python3 audio_bot.py &
# sudo ps aux | grep python

from aiogram import Bot, Dispatcher, executor, types
from gtts import gTTS
from deep_translator import GoogleTranslator



bot = Bot(token="7305513004:AAFDw3aXhZ_JxKQUy6bItbavvyNaYL2pS6c")
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    msg = f'Добро пожаловать!\nОтправьте боту текст и получите аудио на двух языках!'
    await bot.send_message(message.chat.id, msg)


async def text_to_audio(text, language):
    audio = gTTS(text=text, lang=language, slow=False)
    name = f"{language}-{text[:10]}.mp3"
    audio.save(name)
    return name


@dp.message_handler(content_types=['text'])
async def cats(message: types.Message):
    text = message.text
    if text != '':
        path_audio_ru = await text_to_audio(GoogleTranslator(source='auto', target='ru').translate(text), 'ru')
        path_audio_eng = await text_to_audio(GoogleTranslator(source='auto', target='en').translate(text), 'en')
        with open(path_audio_ru, "rb") as audio_ru:
            with open(path_audio_eng, "rb") as audio_eng:
                await bot.send_message(message.chat.id, 'Лови аудио')
                await bot.send_media_group(
                    chat_id=message.chat.id,
                    media=[
                        types.InputMediaDocument(audio_ru),
                        types.InputMediaDocument(audio_eng)
                    ]
                )
    else:
        await bot.send_message(message.chat.id, 'Ты не написал текст')


executor.start_polling(dp, skip_updates=True)

